from hypatia.sources.simbad.ops import get_main_id
from hypatia.sources.nea.db import ExoPlanetStarCollection
from hypatia.sources.simbad.batch import get_star_data_batch
from hypatia.object_params import SingleParam, expected_params_dict, ObjectParams
from hypatia.sources.nea.query import query_nea, set_data_by_host, hypatia_host_name_rank_order, non_parameter_fields
from hypatia.configs.source_settings import (nea_names_the_cause_wrong_simbad_references, nea_ref, known_micro_names,
                                             system_designations)


nea_collection = ExoPlanetStarCollection(collection_name='nea')


def get_nea_data(test_name: str) -> dict or None:
    star_name = get_main_id(test_name, test_origin='nea')
    nea_doc = nea_collection.find_by_id(star_name)
    if nea_doc:
        return nea_doc
    return None


def needs_micro_lense_name_change(nea_name: str) -> None or str:
    nea_name_lower = nea_name.lower()
    if '-' not in nea_name:
        return None
    name_prefix = nea_name_lower.split('-', 1)[0]
    if name_prefix not in known_micro_names:
        return None
    system_designation = ''
    if ' ' in nea_name and nea_name_lower.rsplit(' ', 1)[-1] in system_designations:
        nea_name, system_designation = nea_name.rsplit(' ', 1)
        system_designation = ' ' + system_designation
    if nea_name.lower().endswith('l'):
        return nea_name[:-1] + system_designation
    else:
        return None


def upload_to_database(planets_by_host_name: dict[str, dict[str, any]], test_origin: str = 'nea'):
    # make a list of star-names tuples to be used in the main_id search
    search_ids = []
    has_micro_lens_names = []
    for host_name, host_data in planets_by_host_name.items():
        # every star must have a nea_name that is not empty
        nea_name = host_data['nea_name']
        if not nea_name:
            raise ValueError(
                f'No valid name found for host, this is not supposed to happen, see host_data: {host_data}')
        nea_ids = {host_data[param] for param in hypatia_host_name_rank_order if param in host_data.keys()}
        names_to_try = {nea_id for nea_id in nea_ids if nea_id not in nea_names_the_cause_wrong_simbad_references}
        mirco_name_for_simbad = needs_micro_lense_name_change(nea_name)
        has_micro_lens_name = mirco_name_for_simbad is not None
        if has_micro_lens_name:
            names_to_try = set([mirco_name_for_simbad] + list(names_to_try))
        search_ids.append(tuple(names_to_try))
        has_micro_lens_names.append(has_micro_lens_name)
    # update or get all the name data for these stars from SIMBAD
    star_docs = get_star_data_batch(search_ids=search_ids, test_origin=test_origin,
                                    has_micro_lens_names=has_micro_lens_names)
    nea_docs = []
    for (host_name, host_data), star_doc in zip(planets_by_host_name.items(), star_docs):
        mongo_format = {'_id': star_doc['_id'], 'attr_name': star_doc['attr_name'],
                        'planet_letters': list(host_data['planets'].keys()), **host_data}
        # test that the formating will work when this data is returned from the database, but do not use the returned data
        format_to_hypatia(mongo_format)
        nea_docs.append(mongo_format)
    nea_collection.add_many(nea_docs)


def format_to_hypatia(mongo_format: dict, is_planetary: bool = False) -> dict:
    # do parameter and unit assignment
    hypatia_format = {}
    for param, nea_values in mongo_format.items():
        if param == 'planets':
            planet_data = {planet_letter: format_to_hypatia(planet_values, is_planetary=True)
                           for planet_letter, planet_values in nea_values.items()}
            hypatia_format['planets'] = planet_data
        elif param in non_parameter_fields:
            hypatia_format[param] = nea_values
        elif param in expected_params_dict.keys():
            if is_planetary:
                object_params = hypatia_format.setdefault('planetary', ObjectParams())
            else:
                object_params = hypatia_format.setdefault('stellar', ObjectParams())
            units = expected_params_dict[param]['units']
            if units == 'string':
                object_params[param] = SingleParam.strict_format(param_name=param, value=nea_values,
                                                                 ref=nea_ref, units=units)
            else:
                object_params[param] = SingleParam.strict_format(param_name=param, **nea_values,
                                                                 ref=nea_ref, units=units)
        else:
            raise KeyError(f'Unexpected parameter: {param} in host data: {mongo_format} from NEA. Does this parameter need to be added to the allowed parameters file?')
    return hypatia_format


def refresh_nea_data(verbose: bool = False):
    nea_collection.reset()
    if verbose:
        print('Refreshing NEA data')
    upload_to_database(set_data_by_host(query_nea()))
    if verbose:
        print('NEA data refreshed')


def get_all_nea() -> list[dict[str, any]]:
    """Get all the data from the Hypatia NEA sources in MongoDB"""
    return [format_to_hypatia(mongo_format) for mongo_format in nea_collection.find_all()]


if __name__ == '__main__':
    refresh_nea_data()
    nea_docs_test = get_all_nea()
