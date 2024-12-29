from pymongo.errors import DuplicateKeyError

from hypatia.sources.simbad.db import get_match_name
from hypatia.config import simbad_batch_size, INTERACTIVE_STARNAMES
from hypatia.sources.simbad.tap import get_from_any_ids, get_simbad_from_ids
from hypatia.sources.simbad.ops import (get_simbad_main_id, get_star_data_by_main_id, set_star_doc,
                                        uniquify_star_names, interactive_name_menu, cache_names, get_star_data,
                                        no_simbad_add_name, star_collection, set_cache_data)


def get_star_data_batch(search_ids: list[tuple[str, ...]], test_origin='batch') -> list[dict[str, any]]:
    # step 1: get all the data from the existing star_collection
    star_docs = []
    not_found_ids = {}
    for list_index, search_tuple in list(enumerate(search_ids)):
        found_doc = None
        for single_id in search_tuple:
            possible_main_id = get_simbad_main_id(single_id)
            if possible_main_id is not None:
                found_doc = get_star_data_by_main_id(possible_main_id)
                break
        else:
            not_found_ids[list_index] = (single_id.strip() for single_id in search_tuple)
        star_docs.append(found_doc)
    # step 2: get the data from the SIMBAD API
    # step 2a: unraveled and batch the ids for query to the SIMBAD API
    batched_unraveled_ids = []
    unraveled_ids = set()
    batch_size = 0
    id_to_list_index = {}
    for list_index, search_tuple in not_found_ids.items():
        for single_id in search_tuple:
            batch_size += 1
            unraveled_ids.add(single_id)
            if single_id in id_to_list_index:
                raise ValueError(f"ID {single_id} is in more than one search_tuple")
            id_to_list_index[single_id] = list_index
        if batch_size >= simbad_batch_size:
            batched_unraveled_ids.append(unraveled_ids)
            unraveled_ids = set()
            batch_size = 0
    if unraveled_ids:
        batched_unraveled_ids.append(unraveled_ids)
    # step 2b: query the SIMBAD API for the data
    simbad_not_found_indexes = set()
    for unraveled_ids in batched_unraveled_ids:
        all_list_indexes = {id_to_list_index[single_id] for single_id in unraveled_ids}
        # get the SIMBAD database iod
        results_dict = get_from_any_ids(unraveled_ids)
        # separate into found and not-found by index
        index_to_oid = {}
        oid_to_indexes = {}
        for found_oid_id, found_oid_dict in results_dict.items():
            oid = found_oid_dict['oid']
            list_index = id_to_list_index[found_oid_id]
            if oid in oid_to_indexes.keys():
                oid_to_indexes[oid].add(list_index)
            else:
                oid_to_indexes[oid] = {list_index}
            if list_index in index_to_oid.keys():
                if index_to_oid[list_index] != oid:
                    raise ValueError(f"List index {list_index} has more than one oid")
            else:
                index_to_oid[list_index] = oid
        # Update the not-found indexed for processing after the batching loop
        simbad_not_found_indexes.update(all_list_indexes - set(index_to_oid.keys()))
        # get the other data from the SIMBAD API
        if len(oid_to_indexes) != 0:
            oid_data = get_simbad_from_ids(set(oid_to_indexes.keys()))
            if len(oid_to_indexes) != len(oid_data):
                raise ValueError(f"Length of oid_to_indexes and oid_data do not match")
            # update the star_docs with the new data, one entry per main_id that was found
            for oid, oid_dict in oid_data.items():
                star_data = {**oid_dict}
                simbad_main_id = star_data['main_id']
                # get all the star names from all the aliases that match the main_id
                star_names = list(star_data['aliases'])
                for list_index in oid_to_indexes[oid]:
                    star_names = uniquify_star_names(star_names + list(search_ids[list_index]),
                                                     simbad_main_id=simbad_main_id)
                try:
                    star_doc = set_star_doc(simbad_main_id=star_data['main_id'], star_names=star_names,
                                            star_data=star_data)
                except DuplicateKeyError:
                   star_doc = star_collection.update_aliases(main_id=simbad_main_id, new_aliases=star_names)
                   set_cache_data(simbad_main_id=simbad_main_id, star_record=star_doc,
                                  star_name_aliases=set(star_names))
                for list_index in oid_to_indexes[oid]:
                    star_docs[list_index] = star_doc
    # step 3: prompt the user to add any missing data
    for not_found_index in sorted(simbad_not_found_indexes):
        # try the search ids to see if the cache has the data after other updates
        this_index_search_ids = search_ids[not_found_index]
        for search_id in this_index_search_ids:
            match_name = get_match_name(search_id)
            if match_name in cache_names:
                star_doc = cache_names[match_name]
                break
        else:
            if INTERACTIVE_STARNAMES:
                interactive_name_menu(test_origin=test_origin, aliases=list(this_index_search_ids))
            else:
                no_simbad_add_name(name=this_index_search_ids[0], origin=test_origin,
                                   aliases=list(this_index_search_ids))
            star_doc = get_star_data(test_name=this_index_search_ids[0], test_origin=test_origin)
        star_docs[not_found_index] = star_doc
    return star_docs