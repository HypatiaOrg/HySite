import time

from hypatia.tools.exceptions import StarNameNotFound
from hypatia.database.simbad.query import query_simbad_star
from hypatia.database.simbad.db import StarCollection, indexed_name_types


no_simbad_reset_time_seconds = 60 * 60 * 24 * 365.24  # 1 year
cache_names = {}
cache_docs = {}
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


def set_default_main_id(simbad_main_id: str) -> str:
    """
    Add the SIMBAD main_id to the cache, however if the lowercase version of the main_id is already in the cache,
    then, we return the main_id that was found last time, which might have a different capitalization
    from the SIMBAD database.
    """
    return cache_names.setdefault(simbad_main_id.lower(), simbad_main_id)


def set_cache_data(simbad_main_id: str, star_record: dict[str, any] = None, star_name_aliases: set[str] = None) -> None:
    # make sure the main_id is in the cache
    simbad_main_id = set_default_main_id(simbad_main_id)
    if star_record is not None:
        cache_docs[simbad_main_id] = star_record
    if star_name_aliases is not None:
        if not isinstance(star_name_aliases, set):
            star_name_aliases = set(star_name_aliases)
        # insert the key, with the specified value if it does not exist
        [cache_names.setdefault(alias.lower(), simbad_main_id) for alias in star_name_aliases]


def get_all_star_docs(do_cache_update: bool = True) -> dict[str, any]:
    all_star_docs = star_collection.find_all()
    if do_cache_update:
        for one_doc in all_star_docs:
            simbad_main_id = one_doc["_id"]
            set_cache_data(simbad_main_id=simbad_main_id, star_record=one_doc,
                           star_name_aliases=set(one_doc["aliases"]))
    return {one_doc["_id"]: one_doc for one_doc in all_star_docs}


def uniquify_star_names(star_names: list[str], simbad_main_id: str) -> list[str]:
    """Uniquify the star names in the list and update the cache."""
    unique_set_lower = set()
    unique_list = []
    for name in star_names:
        if name.lower() not in unique_set_lower:
            unique_set_lower.add(name.lower())
            unique_list.append(name)
    # update all the aliases for this star
    set_cache_data(simbad_main_id=simbad_main_id, star_name_aliases=unique_set_lower)
    return sorted(unique_list)


def get_simbad_main_id(test_name: str) -> str | None:
    """Get the main_id for a star name from the cache, return None if the name is not in the cache."""
    return cache_names.get(test_name.lower(), None)


def no_simbad_add_name(name: str, origin: str, aliases: list[str] = None) -> None:
    # asemble the record to add to the database
    if aliases is None:
        aliases = set()
    else:
        aliases = set(aliases)
    if name:
        aliases.add(name)
    star_names_list = list(aliases)
    if not star_names_list:
        raise ValueError("No names were provided to add to the no-SIMBAD database.")
    if not name:
        name = star_names_list[0]
    star_record = {
        "_id": name,
        "attr_name": get_attr_name(name),
        "origin": origin,
        "timestamp": time.time(),
        **parse_indexed_name(star_names_list),
        "aliases": star_names_list,
    }
    # add the main_id to the that database table
    star_collection.add_one(doc=star_record)


ra_dec_fields = {"ra", "dec", "hmsdms"}


def format_simbad_star_record(simbad_main_id: str, star_data: dict[str, any], star_names: list[str]) -> dict[str, any]:
    return {
        "_id": simbad_main_id,
        "attr_name": get_attr_name(simbad_main_id),
        "origin": "simbad",
        "timestamp": time.time(),
        **{field: star_data[field] for field in ra_dec_fields if field in star_data.keys()},
        **parse_indexed_name(star_names),
        "aliases": star_names,
    }


def get_star_data_by_main_id(main_id: str, no_cache: bool = False) -> dict[str, any]:
    if no_cache:
        return star_collection.find_by_id(find_id=main_id)
    cache_doc = cache_docs.get(main_id, None)
    if cache_doc is None:
        cache_doc = star_collection.find_by_id(find_id=main_id)
        cache_docs[main_id] = cache_doc
    return cache_doc


def ask_simbad(test_name: str, original_name: str = None) -> str or None:
    # query SIMBAD for the star data
    simbad_main_id_found, star_names_list, star_data = query_simbad_star(test_name)
    # check if the star data was found
    if simbad_main_id_found is None:
        # no star data was found from SIMBAD
        return None
    # we need to update the cache and the database with the new to skip this step next time
    update_names = {test_name}
    if original_name is not None:
        update_names.add(original_name)
    # is this a new record or an update?
    simbad_main_id_existing = get_simbad_main_id(simbad_main_id_found)
    if simbad_main_id_existing is None:
        # create a cache and database records for this star
        # check for capitalization differences in the main_id
        simbad_main_id = set_default_main_id(simbad_main_id_found)
        # uniquify the star names, and this will update the cache
        star_names = uniquify_star_names(star_names_list + list(update_names), simbad_main_id)
        star_record = format_simbad_star_record(simbad_main_id, star_data, star_names)
        # update the database with the new data
        star_collection.add_one(doc=star_record)
        # update the cache with the new data
        set_cache_data(simbad_main_id=simbad_main_id, star_record=star_record, star_name_aliases=set(star_names))
        # return the main_id
        return simbad_main_id
    # get the existing record from the cache/database
    star_record_existing = get_star_data_by_main_id(simbad_main_id_existing)
    # update the cache and the database with the new data
    simbad_main_id = simbad_main_id_existing
    # uniquify the star names, and this will update the cache
    star_names = uniquify_star_names(star_record_existing['aliases'] + star_names_list + list(update_names),
                                     simbad_main_id)
    star_record = format_simbad_star_record(simbad_main_id, star_data, star_names)
    # update the database with the new data
    # this will replace the existing record with the new one in the cache
    star_record_existing.update(star_record)
    set_cache_data(simbad_main_id=simbad_main_id, star_record=star_record, star_name_aliases=set(star_names))
    # add the main_id to the that database table
    star_collection.update(main_id=simbad_main_id, doc=star_record)
    return simbad_main_id


def interactive_name_menu(test_name: str = '', test_origin: str = 'unknown',  max_tries: int = 5,
                          aliases: list[str] = None) -> str:
    count = 0
    user_response = None
    original_test_name = None
    while count < max_tries:
        if user_response in {'no-simbad', '2'}:
            if original_test_name is None:
                original_test_name = test_name
            no_simbad_add_name(name=original_test_name, origin=test_origin, aliases=aliases)
            return test_name
        elif user_response is not None:
            test_name = user_response
        if test_name == '':
            if original_test_name is not None:
                print(f"This star's test_name: {original_test_name} origin: {test_origin}")
                test_name = original_test_name
            elif aliases is not None:
                print(f"This star's names: {' '.join(aliases)} origin: {test_origin}")
                test_name = aliases[0]
                original_test_name = test_name
        else:
            if user_response is None:
                # we want to save this name to make sure we do not query it when it is seen again.
                original_test_name = test_name
            simbad_main_id = ask_simbad(test_name, original_test_name)
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


def get_main_id(test_name: str, test_origin: str = "unknown", allow_interaction: bool = True) -> str:
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
    if allow_interaction:
        return interactive_name_menu(test_name=test_name, test_origin=test_origin)
    # We will try to query SIMBAD for this star
    simbad_main_id = ask_simbad(test_name)
    if simbad_main_id is None:
        raise StarNameNotFound(f"The star name '{test_name}' {test_origin} was not found in the database.")
    return simbad_main_id


def get_star_data(test_name: str, test_origin: str = "unknown", no_cache: bool = False) -> dict[str, any]:
    main_id = get_main_id(test_name, test_origin)
    return get_star_data_by_main_id(main_id, no_cache)


# preloading the cache with all the star data
get_all_star_docs()

if __name__ == "__main__":
    # star_collection.reset()
    get_main_id("wasp-173 b")
