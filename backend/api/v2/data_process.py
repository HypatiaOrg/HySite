from api.db import hypatia_db, summary_doc, normalizations, catalogs
from hypatia.elements import ElementID, element_rank, elements_that_end_in_h


"""Hard coded API version 2 configurations"""
norm_props = ['notes', 'author', 'year', 'values']
renamed_norms = {
    'and89': 'anders89',
    'asp05': 'asplund05',
    'asp09': 'asplund09',
    'grv98': 'grevesse98',
    'lod09': 'lodders09',
    'grv07': 'grevesse07'
}
catalog_props = ['author', 'year', 'id', 'original_norm_id']
to_v2_catalog_prop_names = {
    'short': 'id',
    'long': 'author',
    'original_norm_id': 'norm',
    'year': 'year',
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

solar_norm_nea = 'lodders09'
elements_nea_raw = ['Fe', 'C', 'O', 'Na', 'Mg', 'Al', 'Si', 'Ca', 'Y', 'Ba_II']
elements_nea = [ElementID.from_str(element) for element in elements_nea_raw]
elements_nea_v2_format = {element_id: str(element_id).replace('_', '') + 'H' for element_id in elements_nea}


null_abundance_record = {'name': 'not-found'}

normalizations_v2 = [{'id': norm_key} | {prop: norm_data[prop] if prop in norm_data.keys() else None
                                         for prop in norm_props}
                     for norm_key, norm_data in normalizations.items()]
# available elemental abundances.
available_elements_v2 = summary_doc['chemicals_uploaded']

# available catalogs
available_catalogs_v2 = []
repeat_count = {}
for cat_dict in [cat_dict for cat_dict in catalogs.values()]:
    author = cat_dict['author']
    if author in repeat_count.keys():
        cat_dict['author'] = f"{author} - Repeat Observations {repeat_count[author]}"
        repeat_count[author] += 1
    else:
        repeat_count[author] = 1
    available_catalogs_v2.append(cat_dict)

# total number of stars in the database
total_stars = len(hypatia_db)

# max unique star names for a query
max_unique_star_names = 10000 + total_stars

# available WDS stars in the database
available_wds_stars = summary_doc['ids_with_wds_names']

# available NEA names in the database
available_nea_names = summary_doc['ids_with_nea_names']

# total number of abundance values in the database
total_abundance_count = hypatia_db.get_abundance_count(norm_key='absolute', by_element=False, count_stars=False)['absolute']

# Representative error values for elements
representative_error = summary_doc['representative_error']


# functions to distribute data
def get_norm_key(norm_key: str) -> str | None:
    norm_key = str(norm_key).lower()
    if norm_key in renamed_norms:
        return renamed_norms[norm_key]
    elif norm_key in normalizations.keys():
        return norm_key
    else:
        return None


def get_norm_data(norm_key: str) -> dict | None:
    norm_key = get_norm_key(norm_key)
    if norm_key is None:
        return None
    return normalizations[norm_key]


def get_catalog_summary(catalog_id: str) -> dict | None:
    catalog_id = str(catalog_id).lower()
    if catalog_id not in catalogs.keys():
        return None
    return catalogs[catalog_id]


def get_star_data_v2(star_names: list[str]) -> list[dict]:
    db_formatted_names_dict = {name: name.replace(' ', '').lower() for name in star_names}
    db_formatted_names = sorted(set(db_formatted_names_dict.values()))
    star_data = {}
    for found_data in hypatia_db.star_data_v2(db_formatted_names=db_formatted_names):
        match_name = found_data.pop('match_name')
        star_data[match_name] = found_data
    for star_name in star_names:
        db_formatted_name = db_formatted_names_dict[star_name]
        star_data_record = v2_null_star_record.copy()
        star_data_record['requested_name'] = star_name
        if db_formatted_name in star_data.keys():
            star_data_record.update(star_data[db_formatted_name])
        yield star_data_record


def element_parse_v2(element_name: str) -> ElementID | None:
    element_name = str(element_name).lower().strip()
    if element_name in elements_that_end_in_h:
        pass
    elif element_name[-1] == 'h':
        element_name = element_name[:-1]
    try:
        return ElementID.from_str(element_name)
    except ValueError:
        return None


def nea_number_format(number: float | None) -> str | None:
    if number is None:
        return None
    else:
        if number == 0.0:
            return '0.00'
        return f"{number:1.2f}"


def format_abundance_record_v2(abundance_record: dict, name: str, match_name: str, all_names: list[str], nea_name: str,
                               solarnorm: str, element: str, do_nea_format: bool = False) -> dict:
    abundance_record['name'] = name
    abundance_record['median_value'] = abundance_record.pop('median', None)
    abundance_record['all_names'] = all_names
    abundance_record['nea_name'] = nea_name
    abundance_record['solarnorm'] = solarnorm
    abundance_record['element'] = element
    by_catalog_values = abundance_record.pop('catalogs', None)
    median_catalogs = abundance_record.pop('median_catalogs', None)
    abundance_record.setdefault('std', None)
    if by_catalog_values is None:
        abundance_record['all_values'] = []
        abundance_record['median'] = []
    else:
        abundance_record['all_values'] = [{'value': float_val, 'catalog': get_catalog_summary(catalog_id)}
                                          for catalog_id, float_val in by_catalog_values.items()]
        if median_catalogs is None:
            abundance_record['median'] = []
        else:
            abundance_record['median'] = [{'value': by_catalog_values[catalog_id],
                                           'catalog': get_catalog_summary(catalog_id)}
                                          for catalog_id in median_catalogs]
    if do_nea_format:
        abundance_record['mean'] = nea_number_format(abundance_record.get('mean', None))
        abundance_record['plusminus_error'] = nea_number_format(abundance_record.get('plusminus_error', None))
        abundance_record['median_value'] = nea_number_format(abundance_record.get('median_value', None))
        abundance_record['num_of_values'] = len(abundance_record['all_values'])
        # 'unknown' is the expected default value from the database query when a nea_name is not found.
        abundance_record['is_planet_host'] = abundance_record.get('nea_name', 'unknown') != 'unknown'
    else:
        abundance_record['match_name'] = match_name
    return abundance_record


def get_abundance_data_v2(
        star_names_db_unique: set[str],
        element_ids_unique: set[ElementID],
        solar_norms_unique: set[str]
        ) -> dict[tuple[str, ElementID, str], dict]:
    # send the database the expected strings and lists for the query.
    db_formatted_names = sorted(star_names_db_unique)
    element_ids_sorted = sorted(element_ids_unique, key=element_rank)
    element_strings_unique = [str(element_id) for element_id in element_ids_sorted]
    solar_norms_unique_sorted = sorted(solar_norms_unique)
    db_results = hypatia_db.abundance_data_v2(
        db_formatted_names=db_formatted_names,
        element_strings_unique=element_strings_unique,
        norm_keys=[norm_key for norm_key in solar_norms_unique_sorted if norm_key != 'absolute'],
        do_absolute='absolute' in solar_norms_unique,
    )
    # pacakge the is where nulls and defaults are added.
    user_packaged_results = {}
    for star_name in db_formatted_names:
        data_this_star = db_results.get(star_name, None)
        if data_this_star is None:
            null_abundance_record_this_star = null_abundance_record | {'match_name': star_name}
            for element_id in element_ids_sorted:
                for solar_norm in solar_norms_unique_sorted:
                    user_data_key = (star_name, element_id, solar_norm)
                    user_packaged_results[user_data_key] = null_abundance_record_this_star
        else:
            name = data_this_star.get('name', None)
            match_name = data_this_star.get('match_name', None)
            all_names = data_this_star.get('all_names', None)
            nea_name = data_this_star.get('nea_name', None)
            for solar_norm in solar_norms_unique_sorted:
                data_this_norm = data_this_star.get(solar_norm, {})
                for element_id, element_str in zip(element_ids_sorted, element_strings_unique):
                    user_data_key = (star_name, element_id, solar_norm)
                    user_packaged_results[user_data_key] = format_abundance_record_v2(
                        abundance_record=data_this_norm.get(element_str, {}),
                        name=name,
                        match_name=match_name,
                        all_names=all_names,
                        nea_name=nea_name,
                        solarnorm=solar_norm,
                        element=element_str,
                    )
    return user_packaged_results


def nea_v2():
    return_list = []
    for star_dict in hypatia_db.nea_v2(solar_norm_nea=solar_norm_nea, elements_nea_v2_format=elements_nea_v2_format):
        name = star_dict['name']
        nea_name = star_dict.get('nea_name', None)
        if nea_name:
            is_planet_host = True
        else:
            is_planet_host = False
        all_names = star_dict['all_names']
        for el_v2_key in elements_nea_v2_format.values():
            el_catalogs = star_dict.get(f'{el_v2_key}_catalogs', None)
            if el_catalogs is None:
                all_values = None
                num_of_values = 0
            else:
                all_values = [{'value': cat_value, 'catalog': get_catalog_summary(catalog_id)}
                              for catalog_id, cat_value in el_catalogs.items()]
                num_of_values = len(all_values)
            el_median_catalogs = star_dict.get(f'{el_v2_key}_median_catalogs', None)
            if el_median_catalogs is None:
                median_catalogs = None
            else:
                median_catalogs = [{'value': el_catalogs[catalog_id], 'catalog': get_catalog_summary(catalog_id)}
                                   for catalog_id in el_median_catalogs]
            mean = star_dict.get(f'{el_v2_key}_mean', None)
            if mean is not None:
                mean = nea_number_format(mean)
            plusminus_error = star_dict.get(f'{el_v2_key}_plusminus_error', None)
            if plusminus_error is not None:
                plusminus_error = nea_number_format(plusminus_error)
            median_value = star_dict.get(f'{el_v2_key}_median_value', None)
            if median_value is not None:
                median_value = nea_number_format(median_value)
            return_list.append(dict(
                name=name,
                all_names=all_names,
                element=el_v2_key,
                solarnorm=solar_norm_nea,
                all_values=all_values,
                median=median_catalogs,
                mean=mean,
                plusminus_error=plusminus_error,
                median_value=median_value,
                num_of_values=num_of_values,
                is_planet_host=is_planet_host,
                nea_name=nea_name,
            ))
    return return_list


if __name__ == '__main__':
    # test_star = get_star_data_v2(star_names=[
    #     "HIP 12345",
    #     "HIP 56789",
    #     "HIP 113044",
    #     "HIP22453",
    #     '*6Lyn',
    #     'hip',
    #   ])

    # test_abundance = get_abundance_data_v2(
    #     star_names_db_unique={'hip12345', 'hip56789', 'hip113044', 'hip22453', '*6lyn'},
    #     element_ids_unique={ElementID.from_str('Fe'), ElementID.from_str('Li'),
    #                         ElementID.from_str('Ti'), ElementID.from_str('baii')},
    #     solar_norms_unique={'lodders09', 'original', 'absolute', 'grevesse07'},
    # )

    test_nea = nea_v2()
