import time

from hypatia.elements import element_rank, ElementID
from hypatia.collect import BaseStarCollection
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
            "aliases": simbad_doc['aliases'],
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

    def count_abundance_measurements(self):
        pass


if __name__ == '__main__':
    hypatiaDB = HypatiaDB(db_name='public', collection_name='hypatiaDB')
    hypatiaDB.reset()  # WARNING: This will delete all data in the collection
