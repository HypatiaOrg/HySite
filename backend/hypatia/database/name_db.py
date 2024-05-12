import time

from hypatia.query.simbad import query_simbad_star
from hypatia.database.collect import StarCollection, indexed_name_types


no_simbad_reset_time_seconds = 60 * 60 * 24 * 365.24  # 1 year
cache_names = {}
star_collection = StarCollection(collection_name="stars")


def get_attr_name(name: str) -> str:
    """Converts a star name into a name that can be used as a database table name or as a Python attribute name."""
    test_name = name.strip().lower().replace(" ", "_")
    while "__" in test_name:
        test_name = test_name.replace("__", "_")
    return test_name.replace("*", "star")\
        .replace("+", "plus").replace("-", "minus")\
        .replace("2mass", "twomass").replace(".", "point")\
        .replace("[", "leftsqbracket").replace("]", "rightsqbracket")\
        .replace(",", "comma")


def parse_indexed_name(star_names: list[str]) -> dict[str, str]:
    indexed_names = {}
    # by sorting the names, the longest names will be checked first.
    for name in sorted(star_names, reverse=True):
        name_lower = name.lower()
        for name_type in indexed_name_types:
            if name_lower.startswith(name_type):
                # only keeps the first (longest) version of a name by the same type
                if name_type not in indexed_names.keys():
                    indexed_names[name_type] = name
                    # break to avoid checking the rest of the name types that cannot match
                    break
    return indexed_names


def uniquify_star_names(star_names: list[str], simbad_main_id: str) -> list[str]:
    """Uniquify the star names in the list and update the cache."""
    unique_set_lower = set()
    unique_list = []
    for name in star_names:
        if name.lower() not in unique_set_lower:
            unique_set_lower.add(name.lower())
            unique_list.append(name)
    # update all the aliases for this star
    cache_update = {alias.lower(): simbad_main_id for alias in unique_set_lower}
    cache_names.update(cache_update)
    return sorted(unique_list)


def ask_simbad(test_name: str) -> str or None:
    has_simbad_name, simbad_main_id, star_names_list, star_data = query_simbad_star(test_name)
    if has_simbad_name:
        # add this name to the name cache
        cache_names[test_name.lower()] = simbad_main_id
        star_names_list.append(test_name)
        # uniquify the star names, and this will update the cache
        star_names = uniquify_star_names(star_names_list, simbad_main_id)
        # asemble the record to add to the database
        star_record = {
            "_id": simbad_main_id,
            "attr_name": get_attr_name(simbad_main_id),
            "origin": "simbad",
            "timestamp": time.time(),
            "ra": star_data['ra'],
            "dec": star_data['dec'],
            "hmsdms": star_data['hmsdms'],
            **parse_indexed_name(star_names),
            "aliases": star_names,
        }
        # add the main_id to the that database table
        star_collection.add_or_update(doc=star_record)
        return simbad_main_id
    else:
        return None


def no_simbad_add_name(name: str, origin: str) -> None:
    # asemble the record to add to the database
    star_names_list = [name]
    star_record = {
        "_id": name,
        "attr_name": get_attr_name(name),
        "origin": origin,
        "timestamp": time.time(),
        **parse_indexed_name(star_names_list),
        "aliases": star_names_list,
    }
    # add the main_id to the that database table
    star_collection.add_or_update(doc=star_record)


def interactive_name_menu(test_name: str = '', test_origin: str = 'unknown',  max_tries: int = 5) -> str:
    count = 0
    user_response = None
    while count < max_tries:
        if user_response in {'no-simbad', '2'}:
            no_simbad_add_name(name=test_name, origin=test_origin)
            return test_name
        elif user_response is not None:
            test_name = user_response
        if test_name != '':
            simbad_main_id = ask_simbad(test_name)
            if simbad_main_id is not None:
                return simbad_main_id
        print(f"This star's test_name: {test_name} origin: {test_origin}")
        print(" is not in the database tables and it was not found on SIMBAD.")
        print("Please select an option (or use control-c to exit):")
        print(" 1. Enter a new name to try to query for SIMBAD (default).")
        print(" 2. Enter 'no-simbad' or '2'")
        print("    to add star name to the no-SIMBAD database.")
        user_response = input("Enter your choice: ").strip()
        count += 1


def get_main_id(test_name, test_origin="unknown") -> str:
    # check if the name has been queried this session.
    test_name_lower = test_name.lower()
    if test_name_lower in cache_names:
        return cache_names[test_name_lower]
    # check if the name is in the database.
    names_doc = star_collection.find_name_match(test_name)
    if names_doc is not None:
        main_id = names_doc["_id"]
        # is this star a known no-SIMBAD star?
        if names_doc['origin'] != "simbad":
            # This star has been in the no-SIMBAD database before
            if names_doc['timestamp'] + no_simbad_reset_time_seconds < time.time():
                # case this star has been in the no-SIMBAD database for too long, let us see id it is in SIMBAD now.
                main_id_possible = ask_simbad(test_name)
                if main_id_possible is None:
                    # No Simbad entry was found, we update the timestamp for when this name was last checked.
                    star_collection.update_timestamp(update_id=main_id)
                else:
                    # We found the star in SIMBAD, let us remove it from the no-SIMBAD database.
                    star_collection.remove_by_id(main_id)
                    # note the cache is already updated in ask_simbad
                    return main_id_possible
        # update all the aliases for this star
        cache_update = {alias.lower(): main_id for alias in names_doc["aliases"]}
        cache_names.update(cache_update)
        return main_id
    # this needs user intervention to continue
    return interactive_name_menu(test_name=test_name, test_origin=test_origin)


def get_star_data(test_name: str, test_origin: str = "unknown") -> dict[str, any]:
    return star_collection.find_by_id(find_id=get_main_id(test_name, test_origin))


if __name__ == "__main__":
    # star_collection.reset()
    get_main_id("wasp-173")
