from hypatia.tools.exceptions import StarNameNotFound
from hypatia.database.nea.query import query_nea, set_data_by_host, hypatia_host_name_rank_order
from hypatia.database.nea.db import ExoPlanetCollection
from hypatia.database.simbad.ops import get_main_id, interactive_name_menu, star_collection, no_simbad_add_name


nea_ref = "NASA Exoplanet Archive"
nea_collection = ExoPlanetCollection(collection_name="nea")
known_micro_names = {"kmt", "ogle", "moa", 'k2'}
system_designations = {'a', 'b', 'c', 'ab', 'ac', 'bc'}
incorrect_nea_names = {'Gaia DR2 4794830231453653888'}
# Gaia DR2 4794830231453653888 is incorrectly associated with HD 41004B in the NEA database,
# but this GAIA name is for HD 41004A, which also has an entry in the NEA database.


def get_nea_data(test_name: str) -> dict or None:
    star_name = get_main_id(test_name)
    nea_doc = nea_collection.find_by_id(star_name)
    if nea_doc:
        return nea_doc
    return None


def needs_micro_lense_name_change(nea_name: str) -> None or str:
    nea_name_lower = nea_name.lower()
    if "-" not in nea_name:
        return None
    name_prefix = nea_name_lower.split("-", 1)[0]
    if name_prefix not in known_micro_names:
        return None
    system_designation = ""
    if " " in nea_name and nea_name_lower.rsplit(" ", 1)[-1] in system_designations:
        nea_name, system_designation = nea_name.rsplit(" ", 1)
        system_designation = " " + system_designation
    if nea_name.lower().endswith("l"):
        return nea_name[:-1] + system_designation
    else:
        return None


def format_for_mongo(host_data: dict) -> dict:
    name_not_found = False
    names_to_try = [host_data[param] for param in hypatia_host_name_rank_order
                    if param in host_data.keys() and host_data[param] not in incorrect_nea_names]
    # every star must have a nea_name that is not empty
    nea_name = host_data['nea_name']
    if not nea_name:
        raise ValueError(f"No valid name found for host, this is not supposed to happen, see host_data: {host_data}")
    mirco_name_for_simbad = needs_micro_lense_name_change(nea_name)
    if mirco_name_for_simbad is not None:
        names_to_try = [mirco_name_for_simbad] + names_to_try
    for available_name in names_to_try:
        try:
            found_id = get_main_id(test_name=available_name, test_origin="nea", allow_interaction=False)
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
            print(f"This star's names ('{"', '".join(names_to_try)}') origin: nea")
            found_id = interactive_name_menu(test_name="", test_origin="nea", aliases=names_to_try)
            # if one name was not found, then we will update all the names to try in the aliases
            star_collection.update_aliases(main_id=found_id, new_aliases=names_to_try)
        else:
            # automatically add the name to the database without a SIMBAD name or a prompt
            no_simbad_add_name(name=nea_name, aliases=names_to_try, origin="nea")
            found_id = get_main_id(test_name=nea_name, test_origin="nea", allow_interaction=False)
    return {"_id": found_id, 'planet_letters': list(host_data['planets'].keys()), **host_data}


def refresh_nea_data(verbose: bool = False):
    nea_collection.reset()
    if verbose:
        print("Refreshing NEA data")
    [nea_collection.add_one(format_for_mongo(host_data)) for host_data in set_data_by_host(query_nea()).values()]
    if verbose:
        print("NEA data refreshed")


if __name__ == '__main__':
    refresh_nea_data()
