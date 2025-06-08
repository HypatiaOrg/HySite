import time

from hypatia.collect import BaseStarCollection
from hypatia.configs.env_load import MONGO_DATABASE, DEBUG
from hypatia.sources.simbad.db import indexed_name_types
from hypatia.elements import element_rank, ElementID, RatioID
from hypatia.sources.simbad.query import simbad_coord_to_deg
from hypatia.pipeline.star.single import SingleStar, ObjectParams
from hypatia.pipeline.star.validator import validator, nea_data, single_abundance_keys
from hypatia.pipeline.star.aggregation import (get_normalization_field, star_data_v2, abundance_data_v2,
                                               frontend_pipeline)


class HypatiaDB(BaseStarCollection):
    added_elements = set()
    added_elements_nlte = set()
    added_catalogs = set()
    added_normalizations = set()
    validator = validator

    def __len__(self):
        return self.collection.count_documents({})

    def create_indexes(self):
        # self.collection_add_index(index_name='_id', ascending=True, unique=True)
        self.collection_add_index(index_name='attr_name', ascending=True, unique=True)
        self.collection_add_index(index_name='ra', ascending=True, unique=False)
        self.collection_add_index(index_name='dec', ascending=True, unique=False)
        self.collection_add_index(index_name='names.match_names', ascending=True, unique=False)
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
            simbad_doc['nea'] = nea['nea_name']

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
            abundance_output = {}
            for norm in reduced_abundances.keys():
                abundance_output_norm = {}
                reduced_this_norm = reduced_abundances[norm]
                for element_name in sorted(reduced_abundances[norm].available_abundances,
                                           key=element_rank):
                    el_stats = reduced_this_norm[element_name]
                    export_cat_data = {}
                    for export_field in single_abundance_keys:
                        try:
                            export_data = getattr(el_stats, export_field)
                        except AttributeError:
                            pass
                        else:
                            if export_data is not None:
                                export_cat_data[export_field] = export_data
                    if export_cat_data:
                        abundance_output_norm[element_name] = export_cat_data
                if abundance_output_norm:
                    abundance_output[norm] = abundance_output_norm
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
            {'$unwind': '$chem_array'},
            {'$group': {'_id': f"{group_id_target}", 'total': {'$sum': sum_target}}},
        ]
        return {doc['_id']: int(doc['total']) for doc in sorted(self.collection.aggregate(json_pipeline),
                                                                key=lambda x: element_rank(ElementID.from_str(x['_id']))
                                                                if by_element
                                                                else lambda x: x['_id'])}

    def find_name_match(self, name: str) -> dict | None:
        return self.collection.find_one({'names.match_names': {"$in": [name]}})

    def get_ids_for_name_type(self, name_type: str) -> list[str]:
        if name_type not in indexed_name_types:
            raise ValueError(f"{name_type} is not a valid name type.")
        return self.collection.find({f'names.{name_type}': {"$exists": True}}).distinct('_id')

    def get_ids_for_nea(self) -> list[str]:
        return self.collection.find({'nea': {"$exists": True}}).distinct('_id')

    def star_data_v2(self, db_formatted_names: list[str]) -> list[dict]:
        json_pipeline = star_data_v2(db_formatted_names=db_formatted_names)
        return self.collection.aggregate(json_pipeline)

    def abundance_data_v2(self, db_formatted_names: list[str],
                          norm_keys: list[str],
                          element_strings_unique: list[str],
                          do_absolute: bool = False) -> dict:

        json_pipeline = abundance_data_v2(db_formatted_names=db_formatted_names, norm_keys=norm_keys,
                                          element_strings_unique=element_strings_unique, do_absolute=do_absolute)
        raw_results = list(self.collection.aggregate(json_pipeline))
        return {doc['match_name']: doc for doc in raw_results}

    def nea_v2(self, solar_norm_nea: str, elements_nea_v2_format: dict[ElementID, str]) -> list[dict]:
        if solar_norm_nea == 'absolute':
            norm_str = 'absolute'
        else:
            norm_str = f'normalizations.{solar_norm_nea}'
        element_fields = {}
        for element_id, el_v2_field in elements_nea_v2_format.items():
            el_path = f'{norm_str}.{element_id}'
            element_fields[f'{el_v2_field}_mean'] = f'${el_path}.mean'
            element_fields[f'{el_v2_field}_catalogs'] = f'${el_path}.catalogs'
            element_fields[f'{el_v2_field}_median_catalogs'] = f'${el_path}.median_catalogs'
            element_fields[f'{el_v2_field}_plusminus_error'] = f'${el_path}.plusminus'
            element_fields[f'{el_v2_field}_median_value'] = f'${el_path}.median'

        json_pipeline = [
            {'$project': {
                '_id': 0,
                'name': '$_id',
                'all_names': '$names.aliases',
                'nea_name': '$nea.nea_name',
                **element_fields,
            }},
        ]
        return list(self.collection.aggregate(json_pipeline))

    def frontend_pipeline(self, db_formatted_names: list[str] = None,
                          db_formatted_names_exclude: bool = False,
                          elements_returned: list[ElementID] = None,
                          elements_match_filters: set[ElementID] = None,
                          element_value_filters: dict[ElementID, tuple[float | None, float | None, bool]] = None,
                          element_ratios_returned: list[RatioID] = None,
                          element_ratios_value_filters: dict[RatioID, tuple[float | None, float | None, bool]] = None,
                          stellar_params_returned: list[str] = None,
                          stellar_params_match_filters: set[str] = None,
                          stellar_params_value_filters: dict[str, tuple[float | None, float | None, bool]] = None,
                          planet_params_returned: list[str] = None,
                          planet_params_match_filters: set[str] = None,
                          planet_params_value_filters: dict[str, tuple[float | None, float | None, bool]] = None,
                          solarnorm_id: str = 'absolute',
                          return_median: bool = True,
                          catalogs: set[str] | None = None,
                          catalog_exclude: bool = False,
                          return_nea_name: bool = False,
                          name_types_returned: list[str] | None = None,
                          sort_field: str | ElementID | None = None,
                          sort_reverse: bool = False,
                          return_error: bool = False,
                          star_name_column: str = 'name',
                          return_hover: bool = False,
                          **kwargs) -> list:
        json_pipeline = frontend_pipeline(
            db_formatted_names=db_formatted_names,
            db_formatted_names_exclude=db_formatted_names_exclude,
            elements_returned=elements_returned,
            elements_match_filters=elements_match_filters,
            element_value_filters=element_value_filters,
            element_ratios_returned=element_ratios_returned,
            element_ratios_value_filters=element_ratios_value_filters,
            stellar_params_returned=stellar_params_returned,
            stellar_params_match_filters=stellar_params_match_filters,
            stellar_params_value_filters=stellar_params_value_filters,
            planet_params_returned=planet_params_returned,
            planet_params_match_filters=planet_params_match_filters,
            planet_params_value_filters=planet_params_value_filters,
            solarnorm_id=solarnorm_id,
            return_median=return_median,
            catalogs=catalogs,
            catalog_exclude=catalog_exclude,
            return_nea_name=return_nea_name,
            name_types_returned=name_types_returned,
            sort_field=sort_field,
            sort_reverse=sort_reverse,
            return_error=return_error,
            star_name_column=star_name_column,
            return_hover=return_hover
        )
        if DEBUG:
            for stage_index, stage in list(enumerate(json_pipeline)):
                print(f'Pipeline Stage {stage_index + 1: 2}):', stage)
        # run the aggregation pipeline and return the results.
        raw_results = list(self.collection.aggregate(json_pipeline))
        return raw_results


if __name__ == '__main__':
    from itertools import product
    hypatiaDB = HypatiaDB(db_name=MONGO_DATABASE, collection_name='hypatiaDB')
    ## Reset the database
    # hypatiaDB.reset()  # WARNING: This will delete all data in the collection
    ## Test the database statistics
    # u_norms = ["absolute", 'lodders09', 'original']
    # u_s_counts = [False, True]
    # u_by_element_counts = [False, True]
    # for index_count, (norm, do_s_count, do_by_el_count) in list(enumerate(product(u_norms, u_s_counts, u_by_element_counts))):
    #     test_return = hypatiaDB.get_abundance_count(norm_key=norm, by_element=do_s_count, count_stars=do_by_el_count)
    #     print(f'{index_count + 1:2}.) Using {norm} norm, counting {"stars" if do_s_count else "abundance measurements"} as a fucntions of {"chemical elements" if do_by_el_count else "The entire database"} ')
    #     print(f'      {test_return}\n')
    ## Test pipeline
    elements_returned=[ElementID.from_str(el_name) for el_name in ['C', 'O', 'Mg', 'Si', 'Ca', 'Ti', 'Fe']]
    element_value_filters={ElementID.from_str('C'): (-1.0, 12.0, False)}
    results = hypatiaDB.frontend_pipeline(
        db_formatted_names=None,
        elements_returned=elements_returned,
        element_value_filters=element_value_filters,)
