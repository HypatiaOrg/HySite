from hypatia.config import INTERACTIVE_STARNAMES
from hypatia.tools.exceptions import StarNameNotFound
from hypatia.sources.nea.db import ExoPlanetStarCollection
from hypatia.object_params import SingleParam, expected_params_dict, ObjectParams
from hypatia.sources.nea.query import (query_nea, set_data_by_host, hypatia_host_name_rank_order, non_parameter_fields,
                                       calculate_nea_row)
from hypatia.sources.simbad.ops import (get_main_id, interactive_name_menu, star_collection, no_simbad_add_name,
                                        get_attr_name, set_cache_data)


nea_ref = 'NASA Exoplanet Archive'
nea_collection = ExoPlanetStarCollection(collection_name='nea')
known_micro_names = {'kmt', 'ogle', 'moa', 'k2'}
system_designations = {'a', 'b', 'c', 'ab', 'ac', 'bc'}
incorrect_nea_names = {'Gaia DR2 4794830231453653888'}
# Gaia DR2 4794830231453653888 is incorrectly associated with HD 41004B in the NEA sources,
# but this GAIA name is for HD 41004A, which also has an entry in the NEA sources.


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


def format_for_mongo(host_data: dict, test_origin: str = 'nea') -> dict:
    name_not_found = False
    names_to_try = [host_data[param] for param in hypatia_host_name_rank_order
                    if param in host_data.keys() and host_data[param] not in incorrect_nea_names]
    # every star must have a nea_name that is not empty
    nea_name = host_data['nea_name']
    if not nea_name:
        raise ValueError(f'No valid name found for host, this is not supposed to happen, see host_data: {host_data}')
    mirco_name_for_simbad = needs_micro_lense_name_change(nea_name)
    if mirco_name_for_simbad is not None:
        names_to_try = [mirco_name_for_simbad] + names_to_try
    for available_name in names_to_try:
        try:
            found_id = get_main_id(test_name=available_name, test_origin=test_origin, allow_interaction=False)
        except StarNameNotFound:
            # move on to the next name but trigger the setting of new aliases
            name_not_found = True
        else:
            if name_not_found:
                # if any names were not found, then we will update all the names to try in the aliases
                star_collection.update_aliases(main_id=found_id, new_aliases=names_to_try)
            # don't keep searching if we found a name
            break
    else:
        # if no name was found, then we will try to interactively find the name
        if mirco_name_for_simbad is None:
            names_str = str("', '".join(names_to_try))
            print(f"This star's names ('{names_str}') origin: nea")
            if INTERACTIVE_STARNAMES:
                found_id = interactive_name_menu(test_name='', test_origin=test_origin, aliases=names_to_try)
                # if one name was not found, then we will update all the names to try in the aliases
                star_doc = star_collection.update_aliases(main_id=found_id, new_aliases=names_to_try)
                set_cache_data(simbad_main_id=found_id, star_record=star_doc,
                               star_name_aliases=set(names_to_try))
            else:
                no_simbad_add_name(name=names_to_try[0], origin=test_origin, aliases=names_to_try)
        else:
            # automatically add the name to the sources without a SIMBAD name or a prompt
            no_simbad_add_name(name=nea_name, aliases=names_to_try, origin='nea')
            found_id = get_main_id(test_name=nea_name, test_origin='nea', allow_interaction=False)
    mongo_format = {'_id': found_id, 'attr_name': get_attr_name(found_id),
                    'planet_letters': list(host_data['planets'].keys()), **host_data}
    # test that the formating will work when this data is returned from the database, but do not use the returned data
    format_to_hypatia(mongo_format)
    return mongo_format


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
    nea_collection.add_many([format_for_mongo(host_data) for host_data in set_data_by_host([calculate_nea_row(row)
                             for row in query_nea()]).values()
                            ])
    if verbose:
        print('NEA data refreshed')


def get_all_nea() -> list[dict[str, any]]:
    """Get all the data from the Hypatia NEA sources in MongoDB"""
    return [format_to_hypatia(mongo_format) for mongo_format in nea_collection.find_all()]


if __name__ == '__main__':
    refresh_nea_data()
    nea_docs = get_all_nea()
