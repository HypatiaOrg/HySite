import time

from hypatia.collect import BaseStarCollection
from hypatia.elements import element_rank, ElementID
from hypatia.sources.simbad.db import validator_star_doc, indexed_name_types
from hypatia.sources.simbad.query import simbad_coord_to_deg
from hypatia.pipeline.star.single import SingleStar, ObjectParams


single_star_param_double = {
    "bsonType": "object",
    "description": "The curated data object for a single-star stellar-parameter",
    "required": ["value", "ref"],
    "additionalProperties": False,
    "properties": {
        "value": {
            "bsonType": "double",
            "description": "The value",
        },
        "ref": {
            "bsonType": "string",
            "description": "The reference citation for the value",
        },
        "err_low": {
            "bsonType": "double",
            "description": "The lower error for the value",
        },
        "err_high": {
            "bsonType": "double",
            "description": "The upper error for the value",
        },
    },
}
single_star_param_int = {
    "bsonType": "object",
    "description": "The curated data object for a single-star stellar-parameter",
    "required": ["value", "ref"],
    "additionalProperties": False,
    "properties": {
        "value": {
            "bsonType": "int",
            "description": "The value",
        },
        "ref": {
            "bsonType": "string",
            "description": "The reference citation for the value",
        },
        "err_low": {
            "bsonType": "int",
            "description": "The lower error for the value",
        },
        "err_high": {
            "bsonType": "int",
            "description": "The upper error for the value",
        },
    },
}
single_star_param_str = {
    "bsonType": "object",
    "description": "The curated data object for a single-star stellar-parameter",
    "required": ["value", "ref"],
    "additionalProperties": False,
    "properties": {
        "value": {
            "bsonType": "string",
            "description": "The value",
        },
        "ref": {
            "bsonType": "string",
            "description": "The reference citation for the value",
        },
    },
}
single_params = [single_star_param_double, single_star_param_int, single_star_param_str]


nea_stellar_or_planetary_params = {
    "bsonType": "object",
    "description": "An object with all the per-star data for a single star",
    "additionalProperties": False,
    "patternProperties": {
        ".+": {"oneOf": single_params},
    },
}

single_abundance = {
    "mean": {
        "bsonType": "double",
        "description": "must be a double and is required"
    },
    "median": {
        "bsonType": "double",
        "description": "must be a double and is required"
    },
    "plusminus": {
        "bsonType": "double",
        "description": "must be a double and is not required"
    },
    "std": {
        "bsonType": "double",
        "description": "must be a double and is not required"
    },
    "min": {
        "bsonType": "double",
        "description": "must be a double and is not required"
    },
    "max": {
        "bsonType": "double",
        "description": "must be a double and is not required"
    },
    "catalogs": {
        "bsonType": "object",
        "description": "These are the raw values pair with the catalog name of the source",
        "additionalProperties": False,
        "patternProperties": {
            ".+": {
                "bsonType": "double",
                "description": "a float value for the abundance",
            },
        },
    },
}
single_abundance_keys = set(single_abundance.keys())
chemical_abundances = {
    "bsonType": "object",
    "description": "Chemical-element abundances",
    "additionalProperties": False,
    "patternProperties": {
        ".+": {
            "bsonType": "object",
            "description": "Data for a single reduced chemical-element abundance",
            "required": ["mean", "median"],
            "additionalProperties": False,
            "properties": single_abundance,
        },
    },
}

abundance_normalizations = {
    "bsonType": "object",
    "description": "The available abundance normalizations",
    "required": ['original'],
    "additionalProperties": False,
    "patternProperties": {
        ".+": chemical_abundances,
    },
}


planet_bson = {
    "bsonType": "object",
    "description": "must be a object that describes a planet",
    "required": ['pl_name', 'letter'],
    "properties": {
        "pl_name": {
            "bsonType": "string",
            "description": "must be a string and is required"
        },
        "letter": {
            "bsonType": "string",
            "description": "must be a string and is required"
        },
        "planetary": nea_stellar_or_planetary_params,
    },
    "additionalProperties": False,
}


nea_data = {
    "nea_name": {
        "bsonType": "string",
        "description": "must be a string and is required and unique"
    },
    "stellar": nea_stellar_or_planetary_params,
    "planet_letters": {
        "bsonType": "array",
        "minItems": 1,
        "description": "must be an array letters for each known planet",
        "items": {
            "bsonType": "string",
            "description": "must be a string planet letter",
        },
    },
    "planets": {
        "bsonType": "object",
        "minItems": 1,
        "description": "must be an object with planet letters as keys",
        "additionalProperties": False,
        "patternProperties": {
            ".+": planet_bson,
        },
    },
}


def get_normalization_field(norm_key: str):
    if norm_key == 'absolute':
        return 'absolute'
    return f'normalizations.{norm_key}'


class HypatiaDB(BaseStarCollection):
    added_elements = set()
    added_elements_nlte = set()
    added_catalogs = set()
    added_normalizations = set()
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "The validator schema for the StarName class",
            "required": ["_id", "attr_name", "timestamp", "aliases"],
            "description": "This is a Star level record for HypatiaCatalog.com the holds abundance and planetary data.",
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required and unique"
                },
                "attr_name": {
                    "bsonType": "string",
                    "description": "must be a string and is required and unique"
                },
                "timestamp": {
                    "bsonType": "double",
                    "description": "must be a double and is required"
                },
                "ra": {
                    "bsonType": "double",
                    "description": "must be a double and is not required"
                },
                "dec": {
                    "bsonType": "double",
                    "description": "must be a double and is not required"
                },
                "hmsdms": {
                    "bsonType": "string",
                    "description": "must be a string and is not required"
                },
                'names': validator_star_doc,
                "aliases": {
                    "bsonType": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "description": "must be an array of string names that this star is known by",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string star name",
                    },
                },
                "stellar": {
                    "bsonType": "object",
                    "description": "An object with all the per-star data for a single star",
                    "additionalProperties": False,
                    "patternProperties": {
                        ".+": {
                            "bsonType": "object",
                            "description": "A data object for a single stellar parameter, such as distance, mass, or radius",
                            "required": ["curated", "all"],
                            "additionalProperties": False,
                            "properties": {
                                "curated": {"oneOf": single_params},
                                "all": {
                                    "bsonType": "array",
                                    "description": "The data records array for a single-star stellar-parameter",
                                    "minItems": 1,
                                    "items": {"oneOf": single_params},
                                },
                            },
                        },
                    },
                },
                "nea": {
                    "bsonType": "object",
                    'description': 'The NASA Exoplanet Archive host-level data object',
                    'required': ['nea_name', "planet_letters", "planets"],
                    'properties': nea_data,
                },
                'absolute': chemical_abundances,
                'normalizations': abundance_normalizations,
                'nlte': {
                    "required": ["absolute"],
                    "description": "The validator schema for NLTE elements ",
                    'properties': {
                        'absolute': chemical_abundances,
                        'normalizations': abundance_normalizations,
                    },
                },
            },
        },
    }

    v2_null_star_record = {
        "status": "not-found",
        "hip": None,
        "hd": None,
        "bd": None,
        "spec": None,
        "vmag": None,
        "bv": None,
        "dist": None,
        "ra": None,
        "dec": None,
        "x": None,
        "y": None,
        "z": None,
        "disk": None,
        "u": None,
        "v": None,
        "w": None,
        "teff": None,
        "logg": None,
        "2MASS": None,
        "ra_proper_motion": None,
        "dec_proper_motion": None,
        "bmag": None,
        "planets": None,
    }

    def create_indexes(self):
        # self.collection_add_index(index_name='_id', ascending=True, unique=True)
        self.collection_add_index(index_name='attr_name', ascending=True, unique=True)
        self.collection_add_index(index_name='ra', ascending=True, unique=False)
        self.collection_add_index(index_name='dec', ascending=True, unique=False)
        self.collection_add_index(index_name='aliases', ascending=True, unique=False)
        # normalization handles
        self.collection_add_index(index_name='normalizations', ascending=True, unique=False)
        # chemical-element names and all nested components
        self.collection_add_index(index_name='normalizations.$**', ascending=True, unique=False)

    def add_star(self, single_star: SingleStar):
        simbad_doc = single_star.simbad_doc
        exo = single_star.exo
        if exo is None:
            nea = None
        else:
            nea = {key: exo[key] for key in nea_data.keys() if key in exo.keys()}
            if "stellar" in exo.keys():
                nea['stellar'] = exo['stellar'].to_record()
            if "planets" in exo.keys():
                nea['planets'] = {}
                for letter, pl_data in exo['planets'].items():
                    nea['planets'][letter] = {
                        name: value.to_record() if isinstance(value, ObjectParams) else value
                        for name, value in pl_data.items()}

        # get the stellar parameters
        stellar = single_star.params.to_record()
        # use the primary coordinates if they exist
        if "raj2000" in stellar.keys() and "dej2000" in stellar.keys():
            ra, dec, hmsdms = simbad_coord_to_deg(ra=stellar["raj2000"]['curated']['value'],
                                                  dec=stellar["dej2000"]['curated']['value'])
        elif "ra" in simbad_doc.keys() and "dec" in simbad_doc.keys():
            ra = simbad_doc['ra']
            dec = simbad_doc['dec']
            hmsdms = simbad_doc['hmsdms']
        else:
            ra = None
            dec = None
            hmsdms = None
        # acquire absolute abundances
        catalogs_this_star = single_star.available_abundance_catalogs
        if len(catalogs_this_star) > 0:
            self.added_catalogs.update(catalogs_this_star)
            reduced_abundances = single_star.reduced_abundances
            abundance_output = {norm: {element_name: {data_key: reduced_abundances[norm][element_name][data_key]
                                                           for data_key
                                                           in reduced_abundances[norm][element_name].__dict__.keys()
                                                           if data_key in single_abundance_keys
                                                           and reduced_abundances[norm][element_name][data_key]
                                                           is not None}
                                       for element_name in sorted(reduced_abundances[norm].available_abundances,
                                                                  key=element_rank)}
                                for norm in reduced_abundances.keys()}
            equilibrium = {}
            non_equilibrium = {}
            for norm_key, element_data in abundance_output.items():
                self.added_normalizations.add(norm_key)
                for element_id, element_record in element_data.items():
                    if element_id.is_nlte:
                        self.added_elements_nlte.add(element_id)
                        simple_name = str(ElementID(name_lower=element_id.name_lower, ion_state=element_id.ion_state,
                                                    is_nlte=False))
                        non_equilibrium.setdefault(norm_key, {})[simple_name] = element_record
                    else:
                        self.added_elements.add(element_id)
                        equilibrium.setdefault(norm_key, {})[str(element_id)] = element_record
            if equilibrium:
                absolute = equilibrium.pop('absolute')
                normalizations = equilibrium
            else:
                absolute = None
                normalizations = None
            if non_equilibrium:
                nlte_abundances = {"absolute": non_equilibrium.pop('absolute')}
                if non_equilibrium:
                    nlte_abundances["normalizations"] = non_equilibrium
            else:
                nlte_abundances = None
        else:
            absolute = None
            normalizations = None
            nlte_abundances = None
        # construct the document with non-None elements
        doc = {
            "_id": simbad_doc['_id'],
            "attr_name": simbad_doc['attr_name'],
            "timestamp": time.time(),
            "aliases": sorted({star_name.replace(' ', '').lower() for star_name in simbad_doc['aliases']}),
            'names': simbad_doc,
        }
        if ra is not None:
            doc['ra'] = ra
        if dec is not None:
            doc['dec'] = dec
        if hmsdms is not None:
            doc['hmsdms'] = hmsdms
        if stellar:
            doc['stellar'] = stellar
        if nea:
            doc['nea'] = nea
        if absolute:
            doc['absolute'] = absolute
        if normalizations:
            doc['normalizations'] = normalizations
        if nlte_abundances:
            doc['nlte'] = nlte_abundances
        self.add_one(doc=doc)
        print(f'Added {simbad_doc["_id"]} to the database')

    def get_abundance_count(self, norm_key: str = 'absolute', by_element: bool = False, count_stars: bool = False)\
            -> dict[str, int]:
        norm_field = get_normalization_field(norm_key)
        if count_stars and not by_element:
            # query is a shortcut, to count stars we can use built-in tools to count documents.
            return {f"{norm_key}": self.collection.count_documents({norm_field: {'$exists': True}})}
        group_id_target = "$chem_array.k" if by_element else f"{norm_key}"
        sum_target = 1 if count_stars else {'$size': {'$objectToArray': "$chem_array.v.catalogs"}}
        json_pipeline = [
            {'$project': {'chem_array': {'$objectToArray': f'${norm_field}'}}},
            {'$unwind': "$chem_array"},
            {'$group': {'_id': f"{group_id_target}", 'total': {'$sum': sum_target}}},
        ]
        return {doc['_id']: int(doc['total']) for doc in sorted(self.collection.aggregate(json_pipeline),
                                                                key=lambda x: element_rank(ElementID.from_str(x['_id']))
                                                                if by_element
                                                                else lambda x: x['_id'])}

    def find_name_match(self, name: str) -> dict | None:
        return self.collection.find_one({'aliases': {"$in": [name]}})

    def get_ids_for_name_type(self, name_type: str) -> list[str]:
        if name_type not in indexed_name_types:
            raise ValueError(f"{name_type} is not a valid name type.")
        return self.collection.find({f'names.{name_type}': {"$exists": True}}).distinct('_id')

    def star_data_v2(self, star_names: list[str]) -> list[dict]:
        db_formatted_names_dict = {name: name.replace(' ', '').lower() for name in star_names}
        db_formatted_names = sorted(set(db_formatted_names_dict.values()))
        json_pipeline = [
            {'$match': {
                'aliases': {
                    '$in': db_formatted_names,
                }
            }},
            {'$project': {
                '_id': 0,
                'name': '$_id',
                'hip': '$names.hip',
                'hd': '$names.hd',
                'bd': '$names.bd',
                '2mass': '$names.2mass',
                'tyc': '$names.tyc',
                'other_names': '$names.aliases',
                'spec': '$stellar.sptype.curated.value',
                'vmag': '$stellar.vmag.curated.value',
                'bv': '$stellar.bv.curated.value',
                'dist': '$stellar.dist.curated.value',
                'ra': '$ra',
                'dec': '$dec',
                'x': '$stellar.x_pos.curated.value',
                'y': '$stellar.y_pos.curated.value',
                'z': '$stellar.z_pos.curated.value',
                'disk': '$stellar.disk.curated.value',
                'u': '$stellar.u_vel.curated.value',
                'v': '$stellar.v_vel.curated.value',
                'w': '$stellar.w_vel.curated.value',
                'teff': '$stellar.teff.curated.value',
                'logg': '$stellar.logg.curated.value',
                'ra_proper_motion': '$stellar.pm_ra.curated.value',
                'dec_proper_motion': '$stellar.pm_dec.curated.value',
                'bmag': '$stellar.bmag.curated.value',
                'planets': {
                    "$map": {
                        "input": {"$objectToArray": "$nea.planets"},
                        "as": 'planet_dict',
                        "in": {
                            'name': '$$planet_dict.v.letter',
                            'm_p': '$$planet_dict.v.planetary.pl_mass.value',
                            'm_p_min_err': '$$planet_dict.v.planetary.pl_mass.err_low',
                            'm_p_max_err': '$$planet_dict.v.planetary.pl_mass.err_high',
                            'p': '$$planet_dict.v.planetary.period.value',
                            'p_min_err': '$$planet_dict.v.planetary.period.err_low',
                            'p_max_err': '$$planet_dict.v.planetary.period.err_high',
                            'e': '$$planet_dict.v.planetary.eccentricity.value',
                            'e_min_err': '$$planet_dict.v.planetary.eccentricity.err_low',
                            'e_max_err': '$$planet_dict.v.planetary.eccentricity.err_high',
                            'a': '$$planet_dict.v.planetary.semi_major_axis.value',
                            'a_min_err': '$$planet_dict.v.planetary.semi_major_axis.err_low',
                            'a_max_err': '$$planet_dict.v.planetary.semi_major_axis.err_high',
                        },
                    },
                },
                'match_name': {
                    '$first': {
                        '$filter': {
                            'input': '$aliases',
                            'as': 'alias',
                            'cond': {'$in': ['$$alias', db_formatted_names]},
                            'limit': 1,
                        },
                    },
                },
                "status": "found",
            }},
        ]
        star_data = {}
        for found_data in self.collection.aggregate(json_pipeline):
            match_name = found_data.pop('match_name')
            star_data[match_name] = found_data
        return_data_list = []
        for star_name in star_names:
            db_formatted_name = db_formatted_names_dict[star_name]
            star_data_record = self.v2_null_star_record.copy()
            star_data_record['requested_name'] = star_name
            if db_formatted_name in star_data.keys():
                star_data_record.update(star_data[db_formatted_name])
            return_data_list.append(star_data_record)
        return return_data_list


def make_iter_zip(u_norms: list, u_s_counts: list, u_by_element_counts: list):
    norm_len = len(u_norms)
    s_count_len = len(u_s_counts)
    by_el_len = len(u_by_element_counts)

    all_norms = u_norms * s_count_len * by_el_len
    half_s_counts = []
    for star_value in u_s_counts:
        half_s_counts.extend(norm_len * [star_value])
    all_s_counts = half_s_counts * by_el_len
    all_by_el_counts = []
    for element_val in u_by_element_counts:
        all_by_el_counts.extend(norm_len * s_count_len * [element_val])
    return zip(all_norms, all_s_counts, all_by_el_counts)


if __name__ == '__main__':
    hypatiaDB = HypatiaDB(db_name='public', collection_name='hypatiaDB')
    # hypatiaDB.reset()  # WARNING: This will delete all data in the collection
    u_norms = ["absolute", 'lodders09', 'original']
    u_s_counts = [False, True]
    u_by_element_counts = [False, True]
    for index_count, (norm, do_s_count, do_by_el_count) in list(enumerate(make_iter_zip(u_norms, u_s_counts, u_by_element_counts))):
        test_return = hypatiaDB.get_abundance_count(norm_key=norm, by_element=do_s_count, count_stars=do_by_el_count)
        print(f'{index_count + 1:2}.) Using {norm} norm, counting {"stars" if do_s_count else "abundance measurements"} as a fucntions of {"chemical elements" if do_by_el_count else "The entire database"} ')
        print(f'      {test_return}\n')
