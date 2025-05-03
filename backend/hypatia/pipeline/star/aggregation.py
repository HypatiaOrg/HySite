from itertools import product

from hypatia.sources.simbad.db import indexed_name_types
from hypatia.elements import element_rank, ElementID, RatioID


str_to_float_fields = {'sptype', 'disk'}
string_names_types = indexed_name_types | {'star_id', 'nea_name', 'planet_letter', 'letter', 'name', 'discovery_method'}
nea_no_ref = {'letter', 'pl_controv_flag', 'pl_name', 'radius_gap', 'discovery_method', 'pl_radelim'}

def add_params_and_filters(match_filters: set[str] | None,
                           value_filters: dict[str, tuple[float | None, float | None, bool]] | None,
                           is_stellar: bool = True, base_path: str = None) -> list[dict]:
    and_filters = []
    curated_path = ''
    if base_path is None:
        if is_stellar:
            base_path = 'stellar.'
            curated_path = '.curated'
        else:
            base_path = 'planets_array.v.planetary.'
    if match_filters:
        for param_name_match in match_filters:
            if param_name_match == 'planet_letter':
                and_filters.append({f'planets_array.v.letter': {'$ne': None}})
            else:
                and_filters.append({f'{base_path}{param_name_match}{curated_path}.value': {'$ne': None}})
    if value_filters:
        for param_name, (min_value, max_value, exclude) in value_filters.items():
            if param_name == 'planet_letter':
                path = 'planets_array.v.letter'
            else:
                path = f'{base_path}{param_name}{curated_path}.value'
            if min_value is not None and max_value is not None:
                if exclude:
                    and_filters.append({'$or': [{path: {'$lt': min_value}},
                                                {path: {'$gt': max_value}}]})
                else:
                    and_filters.append({path: {'$gte': min_value}})
                    and_filters.append({path: {'$lte': max_value}})
            elif min_value is not None:
                if exclude:
                    and_filters.append({path: {'$lt': min_value}})
                else:
                    and_filters.append({path: {'$gte': min_value}})
            elif max_value is not None:
                if exclude:
                    and_filters.append({path: {'$gt': max_value}})
                else:
                    and_filters.append({path: {'$lte': max_value}})
    return and_filters


def get_normalization_field(norm_key: str):
    if norm_key == 'absolute':
        return 'absolute'
    return f'normalizations.{norm_key}'


def pipeline_match_name(db_formatted_names: list[str]):
    return {
        '$first': {
            '$filter': {
                'input': '$names.match_names',
                'as': 'alias',
                'cond': {'$in': ['$$alias', db_formatted_names]},
                'limit': 1,
            },
        },
    }


def pipeline_add_starname_match(db_formatted_names: list[str], exclude: bool = False) -> dict:
    if exclude:
        db_operator = '$nin'
    else:
        db_operator = '$in'
    return {
        '$match': {
            'names.match_names': {
                f'{db_operator}': db_formatted_names,
            }
        }
    }


def catalog_calc_array(element_name: ElementID, norm_path: str, catalogs: list[str], catalog_exclude: bool = False,
                       return_linear: bool = False) -> dict[str, dict]:
    condition = {'$in': ['$$this.k', catalogs]}
    if catalog_exclude:
        condition = {'$not': condition}
    if return_linear:
        obj_name = 'catalogs_linear'
    else:
        obj_name = 'catalogs'
    return {
        '$sortArray': {
            'input': {
                '$filter': {
                    'input': {'$objectToArray': f'${norm_path}.{element_name}.{obj_name}'},
                    'cond': condition,
                },
            },
            'sortBy': {'v': 1},
        }
    }


def star_data_v2(db_formatted_names: list[str]) -> list[dict]:
    return [
        pipeline_add_starname_match(db_formatted_names),
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
            'match_name': pipeline_match_name(db_formatted_names),
            "status": "found",
        }},
    ]


def abundance_data_v2(db_formatted_names: list[str],
                      norm_keys: list[str],
                      element_strings_unique: list[str],
                      do_absolute: bool = False) -> list[dict]:
    requested_fields = {f'{norm_key}.{element_string}': f'$normalizations.{norm_key}.{element_string}'
                        for (norm_key, element_string) in product(set(norm_keys), set(element_strings_unique))}
    if do_absolute:
        for element_string in element_strings_unique:
            requested_fields[f'absolute.{element_string}'] = f'$absolute.{element_string}'
    pipeline_names = pipeline_match_name(db_formatted_names)
    match_name = pipeline_names[0] if isinstance(pipeline_names, list) else pipeline_names
    return [
        pipeline_add_starname_match(db_formatted_names),
        {'$project': {
            '_id': 0,
            'name': '$_id',
            'match_name': match_name,
            'all_names': '$names.aliases',
            'nea_name': {
                '$ifNull': ['$nea.nea_name', "unknown"]
            },
            **requested_fields,
        }},
    ]


def frontend_pipeline(db_formatted_names: list[str] = None,
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
                      ) -> list[dict]:
    if solarnorm_id == 'absolute':
        norm_path = 'absolute'
    else:
        norm_path = f'normalizations.{solarnorm_id}'
    if return_median:
        el_value_path = 'median'
    else:
        el_value_path = 'mean'
    is_planetary = any([planet_params_match_filters, planet_params_returned, planet_params_value_filters])
    catalogs = sorted(catalogs) if catalogs else None
    # get the unique elements
    ratio_elements_set = set()
    ratio_sets = []
    if element_ratios_returned:
        ratio_sets.append(element_ratios_returned)
    if element_ratios_value_filters:
        ratio_sets.extend(element_ratios_value_filters.keys())
    if ratio_sets:
        for element_ratio_id_set in ratio_sets:
            if element_ratio_id_set:
                for element_ratio_id in element_ratio_id_set:
                    ratio_elements_set.add(element_ratio_id.numerator)
                    ratio_elements_set.add(element_ratio_id.denominator)

    all_elements_set = set()
    for element_id_set in [elements_returned, elements_match_filters,
                           element_value_filters.keys(), ratio_elements_set]:
        if element_id_set:
            all_elements_set.update(set(element_id_set))
    all_elements = sorted(all_elements_set, key=element_rank)
    # initialize the pipeline
    json_pipeline = []
    # stage 1: If needed, filter by per-star parameters to narrow the number of documents to process
    and_filters_stellar = []
    if db_formatted_names:
        and_filters_stellar.append({'names.match_names': {f"{'$nin' if db_formatted_names_exclude else '$in'}": db_formatted_names}})
    # add the stellar parameters filters
    and_filters_stellar.extend(add_params_and_filters(match_filters=stellar_params_match_filters,
                                                      value_filters=stellar_params_value_filters, is_stellar=True))
    if is_planetary:
        # only require that a star has at least one planet at this stage.
        and_filters_stellar.append({'nea': {'$ne': None}})
    if and_filters_stellar:
        # only add a pipline stage if there are filters to apply.
        json_pipeline.append({'$match': {"$and": and_filters_stellar}})

    # stage 2: planetary data requires a new-fields, unwind, and match stage to reshape and filter the data.
    if is_planetary:
        # stage 2a: reshape the planetary data to be an array of objects, which can be a targe for unwind
        json_pipeline.append({'$addFields': {'planets_array': {'$objectToArray': '$nea.planets'}}})
        # stage 2b: unwind the planetary data to allow for per-planet filtering
        json_pipeline.append({'$unwind': '$planets_array'})
        # stage 2c: per-planetary data match and range filtering
        and_filters_planetary = add_params_and_filters(match_filters=planet_params_match_filters,
                                                       value_filters=planet_params_value_filters, is_stellar=False)
        if and_filters_planetary:
            # only add a pipline stage if there are filters to apply.
            json_pipeline.append({'$match': {'$and': and_filters_planetary}})

    # stage 3: element not null, optional catalog filtering.
    if catalogs:
        # stage 3-catalogs: we need to find or exclude values from specific catalogs and calculate the median/mean
        # get the values for in a two-step calculation; the first is to sort the values
        add_fields_first_calc = {}
        for element_name in all_elements:
            add_fields_first_calc[f'{element_name}_cat_array'] = catalog_calc_array(
                element_name=element_name, norm_path=norm_path, catalogs=catalogs,
                catalog_exclude=catalog_exclude,
                return_linear=False)
            if not return_median:
                add_fields_first_calc[f'{element_name}_cat_array_linear'] = catalog_calc_array(
                    element_name=element_name, norm_path=norm_path, catalogs=catalogs,
                    catalog_exclude=catalog_exclude,
                    return_linear=True)


        # calculate the median/meaning and error values from the sorted in the first step of the calculation
        add_fields_final_calc = {}
        array_suffix = '_linear' if not return_median else ''
        for element_name in all_elements:
            values_array = {
                '$map': {
                    'input': f'${element_name}_cat_array{array_suffix}',
                    'in': '$$this.v',
                },
            }
            # calculate the median/mean and error values
            if return_median:
                cat_calc = {
                    '$median': {
                        'input': values_array,
                        'method': 'approximate',
                    },
                }
            else:
                cat_calc = {'$log10': {'$avg': values_array}}
            add_fields_final_calc[f'{element_name}'] = cat_calc
            add_fields_final_calc[f'{element_name}_catalogs'] = {'$arrayToObject': f'${element_name}_cat_array'}
            if return_error:
                add_fields_final_calc[f'{element_name}'] = {'$round': [cat_calc, 2]}

                # calculate the error values
                add_fields_final_calc[f'{element_name}_err'] = {
                    '$round': [{
                        '$divide': [
                            {'$subtract': [{'$max': values_array}, {'$min': values_array}]},
                            2.0,
                        ],
                    }, 2]
                }

        # package the results as two aggregation stages
        if add_fields_first_calc:
            json_pipeline.append({'$addFields': add_fields_first_calc})
        if add_fields_final_calc:
            json_pipeline.append({'$addFields': add_fields_final_calc})
    else:
        # stage 3-no-catalogs: make new field names for the elements
        add_fields = {}
        for element_name in all_elements:
            element_field_name = str(element_name)
            add_fields[element_field_name] = f'${norm_path}.{element_field_name}.{el_value_path}'
            add_fields[f'{element_field_name}_catalogs'] = {
                '$arrayToObject': {
                    '$sortArray': {
                        'input': {'$objectToArray': f'${norm_path}.{element_field_name}.catalogs'},
                        'sortBy': {'v': 1},
                    }
                }
            }
            if return_error:
                add_fields[f'{element_field_name}_err'] = f'${norm_path}.{element_field_name}.plusminus'
        json_pipeline.append({'$addFields': add_fields})

    # stage 4: element match and value filtering
    and_filters_elements = []
    if elements_match_filters:
        for element_name in sorted(elements_match_filters, key=element_rank):
            and_filters_elements.append({f'{element_name}': {'$ne': None}})
    if element_value_filters:
        for element_name, (min_val, max_val, exclude) in element_value_filters.items():
            if min_val is not None and max_val is not None:
                if exclude:
                    and_filters_elements.append({'$or': [{f'{element_name}.{el_value_path}': {'$lt': min_val}},
                                                {f'{element_name}.{el_value_path}': {'$gt': max_val}}]})
                else:
                    and_filters_elements.append({f'{element_name}.{el_value_path}': {'$gte': min_val}})
                    and_filters_elements.append({f'{element_name}.{el_value_path}': {'$lte': max_val}})
    if and_filters_elements:
        json_pipeline.append({'$match': {'$and': and_filters_elements}})

    # stage 5 ratio calculation
    add_fields_ratio = {}
    if element_ratios_returned or element_ratios_value_filters:
        for ratio_id in list(element_ratios_returned | element_ratios_value_filters.keys()):
            ratio_str = f'{ratio_id.numerator}_{ratio_id.denominator}'
            add_fields_ratio[ratio_str] = {
                '$round': [{
                    '$subtract': [f'${norm_path}.{ratio_id.numerator}.{el_value_path}',
                                  f'${norm_path}.{ratio_id.denominator}.{el_value_path}']}, 2]
            }
    if add_fields_ratio:
        json_pipeline.append({'$addFields': add_fields_ratio})

    # stage 6: elemental-ratio float-value filtering
    if element_ratios_value_filters:
        and_filters_ratios = add_params_and_filters(
            match_filters=None,
            value_filters={f'{ratio_id.numerator}_{ratio_id.denominator}': filter_vals
                           for ratio_id, filter_vals in element_ratios_value_filters.items()},
            base_path='',
        )
        if and_filters_ratios:
            json_pipeline.append({'$match': {'$and': and_filters_ratios}})

    # stage 7: project the final data
    return_doc = {
        '_id': 0,
        f'{star_name_column}': '$_id',
    }

    if elements_returned:
        for element_name in sorted(elements_returned, key=element_rank):
            element_str = str(element_name)
            return_doc[element_str] = 1
            if return_error:
                return_doc[f'{element_str}_err'] = 1
    if element_ratios_returned:
        for ratio_id in element_ratios_returned:
            return_doc[f'{ratio_id.numerator}_{ratio_id.denominator}'] = 1
    if stellar_params_returned:
        for param_name in stellar_params_returned:
            # parameter's value
            return_doc[param_name] = f'$stellar.{param_name}.curated.value'
            # parameter's error
            if return_error and param_name not in string_names_types:
                return_doc[f'{param_name}_err'] = f'$stellar.{param_name}.curated.err'
            # return the hover reference
            if return_hover:
                return_doc[f'{param_name}_ref'] = f'$stellar.{param_name}.curated.ref'
            # sorting by a string field requires a different field to sort by.
            if sort_field == param_name and param_name in str_to_float_fields:
                number_field_str = f'{param_name}_num'
                return_doc[number_field_str] = f'$stellar.{number_field_str}.curated.value'
                sort_field = number_field_str

    if is_planetary:
        return_doc['nea_name'] = '$planets_array.v.pl_name'
        if planet_params_returned:
            for param_name in planet_params_returned:
                if param_name not in {'pl_name', 'nea_name'}:
                    if param_name == 'planet_letter':
                        return_doc[param_name] = '$planets_array.v.letter'
                    elif param_name in string_names_types:
                        return_doc[param_name] = f'$planets_array.v.planetary.{param_name}.value'
                    else:
                        return_doc[param_name] = f'$planets_array.v.planetary.{param_name}.value'
                        if return_error:
                            return_doc[f'{param_name}_err'] = f'$planets_array.v.planetary.{param_name}.err'
                    if return_hover and param_name not in nea_no_ref:
                        return_doc[f'{param_name}_ref'] = f'$planets_array.v.planetary.{param_name}.ref'
    elif return_nea_name:
        return_doc['nea_name'] = '$nea.nea_name'
    if name_types_returned:
        for name_type in name_types_returned:
            if name_type != star_name_column:
                return_doc[name_type] = f'$names.{name_type}'
    if return_hover:
        if elements_returned:
            for element_name in sorted(elements_returned, key=element_rank):
                return_doc[f'{element_name}_catalogs'] = 1
    if sort_field:
        sort_location = return_doc[sort_field]
        if sort_location == 1:
            sort_location = f'${sort_field}'
        # use this to sort null fields to the end of the list.
        return_doc['sort_field_type'] = {'$type': f'{sort_location}'}
    json_pipeline.append({'$project': return_doc})

    # Stage 8: sort the data
    if sort_field:
        # adding the star_name_column or nea_name to the sort field to ensure a stable sort.
        sort_dict = {
            'sort_field_type': -1 if sort_field in string_names_types else 1,
            f'{sort_field}': -1 if sort_reverse else 1,
        }
        unique_field = 'nea_name' if is_planetary else str(star_name_column)
        if unique_field != sort_field:
            sort_dict[unique_field] = 1
        json_pipeline.append({'$sort': sort_dict})
    return json_pipeline
