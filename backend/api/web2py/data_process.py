from copy import copy

import numpy as np

from api.db import summary_doc, hypatia_db
from hypatia.pipeline.star.aggregation import string_names_types
from hypatia.elements import ElementID, RatioID, hydrogen_id, get_representative_error, element_rank
from api.v2.data_process import (get_norm_key, get_norm_data, get_catalog_summary, total_stars, total_abundance_count,
                                 available_wds_stars, available_nea_names, available_elements_v2, available_catalogs_v2,
                                 normalizations_v2)


stellar_param_types_v2 = ['raj2000', 'decj2000', 'dist', 'x_pos', 'y_pos', 'z_pos', 'teff', 'logg',
                          'sptype', 'vmag', 'bmag', 'bv', 'pm_ra', 'pm_dec', 'u_vel', 'v_vel', 'w_vel',
                          'disk', 'mass', 'rad']
stellar_param_types_v2_set = set(stellar_param_types_v2)
planet_param_types_v2 = ["semi_major_axis", "eccentricity", "inclination", "pl_mass", "pl_radius", 'planet_letter',]
planet_param_types_v2_set = set(planet_param_types_v2)
ranked_string_params = {'sptype': 'sptype_num', 'disk': 'disk_num'}
nones = {None, 'none', ''}
none_denominators = {None, 'none', '', 'h', 'H'}
true_set = {"true", 1, 1.0, '1.0', '1', 't', 'yes', 'y', 'on', True}

home_data = {
    'stars': total_stars,
    'stars_with_planets': len(available_nea_names),
    'stars_multistar': len(available_wds_stars),
    'elements': len(available_elements_v2),
    'catalogs': len(available_catalogs_v2),
    'abundances': total_abundance_count,
}

units_and_fields = summary_doc['units_and_fields']
units_and_fields_v2 = {a_param: units_and_fields[a_param] for a_param
                       in stellar_param_types_v2 + planet_param_types_v2 + list(ranked_string_params.values())}

plot_norms = [{k: v for k, v in s_norm.items() if k != 'values'} for s_norm in normalizations_v2]
chemical_ref = summary_doc['chemical_ref']


element_data = []
for element_str_id in available_elements_v2:
    element_id = ElementID.from_str(element_str_id)
    ref_this_el = chemical_ref[element_id.name_lower]
    if element_id.ion_state is None:
        abbreviation = ref_this_el['abbreviation']
        element_name = ref_this_el['element_name']
    else:
        upper_ion_state = element_id.ion_state.upper()
        abbreviation = f"{ref_this_el['abbreviation']} ({element_id.ion_state.upper()})"
        element_name = f"{ref_this_el['element_name']} ({element_id.ion_state.upper()})"
    element_data.append({
        'element_id': element_str_id,
        'element_name': element_name,
        'abbreviation': abbreviation,
    })


def is_true_str(test: str) -> bool:
    if isinstance(test, str):
        test = test.lower()
    if test in true_set:
        return True
    return False


def is_list_str(test: str | None, use_lower: bool = True) -> list[str] | None:
    if test in nones:
        return None
    if isinstance(test, str):
        test_lower = test.lower()
        if use_lower:
            test = test_lower
        if test_lower in nones:
            return None
        if ';' not in test and ',' in test and 'wds' not in test:
            delimiter = ','
        else:
            delimiter = ';'
        return [name.strip() for name in test.split(delimiter)]
    else:
        raise TypeError(f"Expected a string, got {type(test)} in is_list_str()")


def is_none_str(test: str | None, default: str | None, use_lower: bool = True) -> str | None:
    if test in nones:
        return default
    elif isinstance(test, str):
        test_lower = test.lower()
        if test_lower in nones:
            return default
        elif use_lower:
            return test_lower
        else:
            return test
    else:
        raise TypeError(f"Expected a string, got {type(test)} in is_none_str()")


def is_value_str(test: str | None) -> float | str | None:
    try:
        return float(test)
    except ValueError:
        pass
    except TypeError:
        pass
    return is_none_str(test, None)


class ParameterFilters:
    def __init__(self, axis_num: int | None,
                 name: str,
                 divisor_element: str,
                 filter_low: float | None = None,
                 filter_high: float | None = None,
                 exclude: bool = False):
        self.axis_num = axis_num
        self.name = name
        self.filter1 = name
        self.exclude = exclude
        self.divisor_element = None
        self.filter2 = None
        self.filter_low = None
        self.filter3 = None
        self.filter_high = None
        self.filter4 = None
        if name == 'none':
            self.filter_needed = False
            self.type = None
        else:
            self.filter_needed = True
            if name in planet_param_types_v2_set:
                self.type = 'planet'
            elif name in stellar_param_types_v2_set:
                self.type = 'stellar'
            else:
                self.type = 'element'
                self.name = ElementID.from_str(name)
                self.filter1 = self.name
                divisor_element_id = ElementID.from_str(divisor_element)
                if divisor_element_id != hydrogen_id:
                    self.divisor_element = str(divisor_element_id)
            if filter_low is not None and filter_low is not None:
                filter_low = float(filter_low)
                filter_high = float(filter_high)
                if filter_low > filter_high:
                    filter_low, filter_high = filter_high, filter_low
            if filter_low is not None or filter_high is not None:
                self.filter_low = float(filter_low)
                self.filter_high = float(filter_high)


def determine_param_type(param_name: str, denominator_element: str = None) -> tuple[str, str | ElementID | RatioID]:
    if param_name in planet_param_types_v2_set:
        return 'planet', param_name
    elif param_name in stellar_param_types_v2_set:
        return 'stellar', param_name
    elif denominator_element is not None and denominator_element != 'none' and denominator_element.lower() != 'h':
        return 'element_ratio', RatioID.from_str(numerator_element=param_name, denominator_element=denominator_element)
    else:
        return 'element', ElementID.from_str(param_name)


class FilterForQuery:
    def __init__(self):
        # define variables
        self.elements_returned = []
        self.elements_match_filters = set()
        self.element_value_filters = {}
        self.element_ratios_returned = []
        self.element_ratios_value_filters = {}
        self.stellar_params_returned = []
        self.stellar_params_match_filters = set()
        self.stellar_params_value_filters = {}
        self.planet_params_returned = []
        self.planet_params_match_filters = set()
        self.planet_params_value_filters = {}

    def add_match_filter(self, param_type: str, param_id: str | ElementID | RatioID, is_axis_type: bool = True):
        if param_type == 'element':
            if is_axis_type:
                self.elements_returned.append(param_id)
            self.elements_match_filters.add(param_id)
        elif param_type == 'element_ratio':
            if is_axis_type:
                self.element_ratios_returned.append(param_id)
            self.elements_match_filters.add(param_id.numerator)
            self.elements_match_filters.add(param_id.denominator)
        elif param_type == 'stellar':
            if is_axis_type:
                self.stellar_params_returned.append(param_id)
            self.stellar_params_match_filters.add(param_id)
        elif param_type == 'planet':
            if is_axis_type:
                self.planet_params_returned.append(param_id)
            self.planet_params_match_filters.add(param_id)

    def set_range_filter(self, param_type:str, param_id: str,
                         filter_low: float | None = None, filter_high: float | None = None, exclude: bool = False):
        if filter_low is None and filter_high is None:
            # with no floats to restrict the ranges of values, all that is needed is a match filter
            self.add_match_filter(param_type=param_type, param_id=param_id, is_axis_type=False)
            return
        if param_id == 'sptype':
            param_id = 'sptype_num'
        elif param_id == 'disk':
            param_id = 'disk_num'
        # ensure the types are of the filter_low and filter_high are either float or None
        if filter_low is not None and filter_high is not None:
            try:
                filter_low = float(filter_low)
                filter_high = float(filter_high)
            except ValueError:
                pass
            else:
                if filter_low > filter_high:
                    filter_low, filter_high = filter_high, filter_low
        elif filter_low is not None:
            try:
                filter_low = float(filter_low)
            except ValueError:
                pass
        elif filter_high is not None:
            try:
                filter_high = float(filter_high)
            except ValueError:
                pass
        if param_type == 'element':
            self.element_value_filters[param_id] = (filter_low, filter_high, exclude)
        elif param_type == 'element_ratio':
            # filtering for ratios is done in multiple stages:
            # 1. a match filter to get the required elements
            self.add_match_filter(param_type='element_ratio', param_id=param_id, is_axis_type=False)
            # 2. a range filter after the ratio values are calculated
            self.element_ratios_value_filters[param_id] = (filter_low, filter_high, exclude)
        elif param_type == 'stellar':
            self.stellar_params_value_filters[param_id] = (filter_low, filter_high, exclude)
        elif param_type == 'planet':
            self.planet_params_value_filters[param_id] = (filter_low, filter_high, exclude)


def graph_settings_from_request(settings: dict[str, any]):
    filter1_1 = is_none_str(settings.get('filter1_1', None), default=None)
    filter1_2 = is_none_str(settings.get('filter1_2', None), default='H')
    filter1_3 = is_value_str(settings.get('filter1_3', None))
    filter1_4 = is_value_str(settings.get('filter1_4', None))
    filter2_1 = is_none_str(settings.get('filter2_1', None), default=None)
    filter2_2 = is_none_str(settings.get('filter2_2', None), default='H')
    filter2_3 = is_value_str(settings.get('filter2_3', None))
    filter2_4 = is_value_str(settings.get('filter2_4', None))
    filter3_1 = is_none_str(settings.get('filter3_1', None), default=None)
    filter3_2 = is_none_str(settings.get('filter3_2', None), default='H')
    filter3_3 = is_value_str(settings.get('filter3_3', None))
    filter3_4 = is_value_str(settings.get('filter3_4', None))
    xaxis1 = is_none_str(settings.get('xaxis1', None), default='Fe')
    xaxis2 = is_none_str(settings.get('xaxis2', None), default='H')
    yaxis1 = is_none_str(settings.get('yaxis1', None), default='Si')
    yaxis2 = is_none_str(settings.get('yaxis2', None), default='H')
    zaxis1 = is_none_str(settings.get('zaxis1', None), default=None)
    zaxis2 = is_none_str(settings.get('zaxis2', None), default='H')
    cat_action = is_none_str(settings.get('cat_action', None), default='exclude')
    star_action = is_none_str(settings.get('star_action', None), default='exclude')
    filter1_inv = is_true_str(settings.get('filter1_inv', 'false'))
    filter2_inv = is_true_str(settings.get('filter2_inv', 'false'))
    filter3_inv = is_true_str(settings.get('filter3_inv', 'false'))
    solarnorm_id = get_norm_key(is_none_str(settings.get('solarnorm', None), default='lodders09'))
    statistic = settings.get('statistic', None)
    return_nea_name = is_true_str(settings.get('return_nea_name', 'false'))
    if statistic is None:
        return_median = is_true_str(settings.get('return_median', 'true'))
    else:
        return_median = str(is_none_str(statistic, default='median')).lower() == 'median'
    normalize = is_true_str(settings.get('normalize', 'false'))
    if solarnorm_id is None:
        solarnorm_id = 'lodders09'

    raw_cat = copy(is_none_str(settings.get('catalogs', None), default=None))
    if raw_cat is None:
        catalogs = None
    elif isinstance(raw_cat, str):
        parse_cats = (raw_cat.replace(' ', '').replace(',', ';').replace('\'', '')
                      .replace('[', '').replace(']', ''))
        catalogs = sorted({cat_data['id'] for cat_data
                           in [get_catalog_summary(raw_name) for raw_name in parse_cats.split(';')]
                           if cat_data is not None})
    else:
        catalogs = sorted({cat_data['id'] for cat_data
                           in [get_catalog_summary(raw_name) for raw_name in raw_cat]
                           if cat_data is not None})
    mode = settings.get('mode', None)
    is_histogram = mode == 'hist'

    star_list = is_list_str(settings.get('star_list', None))
    filters_list = [
        (filter1_1, filter1_2, filter1_3, filter1_4, filter1_inv),
        (filter2_1, filter2_2, filter2_3, filter2_4, filter2_inv),
        (filter3_1, filter3_2, filter3_3, filter3_4, filter3_inv),
    ]
    filter_for_query = FilterForQuery()
    # paras the axis make iterables that are in the form of the final returned data product
    axis_mapping = {'x': determine_param_type(param_name=xaxis1, denominator_element=xaxis2)}
    if mode == 'scatter':
        axis_mapping['y'] = determine_param_type(param_name=yaxis1, denominator_element=yaxis2)
        if zaxis1 not in nones:
            axis_mapping['z'] = determine_param_type(param_name=zaxis1, denominator_element=zaxis2)
    # get the returned data types and the base filtering need to return these data types
    [filter_for_query.add_match_filter(param_type=param_type, param_id=param_id)
     for param_type, param_id in axis_mapping.values()]
    # add other filtering for both matching and value filtering
    for param_id, denominator_element, filter_low, filter_high, exclude in filters_list:
        if param_id not in nones:
            param_type, param_id = determine_param_type(param_name=param_id, denominator_element=denominator_element)
            filter_for_query.set_range_filter(
                param_type=param_type, param_id=param_id,
                filter_low=filter_low, filter_high=filter_high, exclude=exclude)
    if star_list:
        db_formatted_names = sorted({name.replace(' ', '').lower() for name in star_list})
    else:
        db_formatted_names = None
    db_formatted_names_exclude = star_action == "exclude"
    catalog_exclude = cat_action == "exclude"
    return_nea_name = return_nea_name or mode == 'hist'
    solarnorm_id = get_norm_key(solarnorm_id)
    return dict(
        db_formatted_names=db_formatted_names,
        db_formatted_names_exclude=db_formatted_names_exclude,
        elements_returned=filter_for_query.elements_returned,
        elements_match_filters=filter_for_query.elements_match_filters,
        element_value_filters=filter_for_query.element_value_filters,
        element_ratios_returned=filter_for_query.element_ratios_returned,
        element_ratios_value_filters=filter_for_query.element_ratios_value_filters,
        stellar_params_returned=filter_for_query.stellar_params_returned,
        stellar_params_match_filters=filter_for_query.stellar_params_match_filters,
        stellar_params_value_filters=filter_for_query.stellar_params_value_filters,
        planet_params_returned=filter_for_query.planet_params_returned,
        planet_params_match_filters=filter_for_query.planet_params_match_filters,
        planet_params_value_filters=filter_for_query.planet_params_value_filters,
        solarnorm_id=solarnorm_id,
        return_median=return_median,
        catalogs=catalogs,
        catalog_exclude=catalog_exclude,
        return_nea_name=return_nea_name,
        axis_mapping=axis_mapping,
        is_histogram=is_histogram,
        normalize_hist=normalize,
    )


def table_settings_from_request(settings: dict[str, any]) -> dict[str, any]:
    graph_settings = graph_settings_from_request(settings=settings)
    requested_name_types = is_list_str(settings.get('requested_name_types', None))
    requested_stellar_params = is_list_str(settings.get('requested_stellar_params', None))
    requested_planet_params = is_list_str(settings.get('requested_planet_params', None))
    requested_elements = is_list_str(settings.get('requested_elements', None), use_lower=False)
    if requested_elements is not None:
        requested_elements = [ElementID.from_str(el_name) for el_name in requested_elements]
    sort_field = is_none_str(settings.get('sort', None), default=None, use_lower=False)
    sort_reverse = is_true_str(settings.get('reverse', 'false'))
    show_error = is_true_str(settings.get('show_error', 'false'))
    show_hover = is_true_str(settings.get('show_hover', 'false'))

    return dict(
        db_formatted_names=graph_settings['db_formatted_names'],
        db_formatted_names_exclude=graph_settings['db_formatted_names_exclude'],
        elements_match_filters=graph_settings['elements_match_filters'],
        element_value_filters=graph_settings['element_value_filters'],
        element_ratios_value_filters=graph_settings['element_ratios_value_filters'],
        stellar_params_match_filters=graph_settings['stellar_params_match_filters'],
        stellar_params_value_filters=graph_settings['stellar_params_value_filters'],
        planet_params_match_filters=graph_settings['planet_params_match_filters'],
        planet_params_value_filters=graph_settings['planet_params_value_filters'],
        solarnorm_id=graph_settings['solarnorm_id'],
        return_median=graph_settings['return_median'],
        catalogs=graph_settings['catalogs'],
        catalog_exclude=graph_settings['catalog_exclude'],
        name_types_returned=requested_name_types,
        stellar_params_returned=requested_stellar_params,
        planet_params_returned=requested_planet_params,
        elements_returned=requested_elements,
        sort_field=sort_field,
        sort_reverse=sort_reverse,
        return_error=show_error,
        return_hover=show_hover,
    )


def graph_query_from_request(settings: dict[str, any], from_api: bool = False) -> dict[str, any]:
    # parse the settings from the request for the graph query
    graph_settings = graph_settings_from_request(settings=settings)
    # get the data from the database
    planet_params_returned = graph_settings['planet_params_returned']
    planet_params_match_filters = graph_settings['planet_params_match_filters']
    planet_params_value_filters = graph_settings['planet_params_value_filters']
    graph_data = hypatia_db.frontend_pipeline(
        db_formatted_names=graph_settings['db_formatted_names'],
        db_formatted_names_exclude=graph_settings['db_formatted_names_exclude'],
        elements_returned=graph_settings['elements_returned'],
        elements_match_filters=graph_settings['elements_match_filters'],
        element_value_filters=graph_settings['element_value_filters'],
        element_ratios_returned=graph_settings['element_ratios_returned'],
        element_ratios_value_filters=graph_settings['element_ratios_value_filters'],
        stellar_params_returned=graph_settings['stellar_params_returned'],
        stellar_params_match_filters=graph_settings['stellar_params_match_filters'],
        stellar_params_value_filters=graph_settings['stellar_params_value_filters'],
        planet_params_returned=planet_params_returned,
        planet_params_match_filters=planet_params_match_filters,
        planet_params_value_filters=planet_params_value_filters,
        solarnorm_id=graph_settings['solarnorm_id'],
        return_median=graph_settings['return_median'],
        catalogs=graph_settings['catalogs'],
        catalog_exclude=graph_settings['catalog_exclude'],
        return_nea_name=graph_settings['return_nea_name'],
    )
    # get more settings about how to process the data
    axis_mapping = graph_settings['axis_mapping']
    solarnorm_id = graph_settings['solarnorm_id']
    is_histogram = graph_settings['is_histogram']
    normalize_hist = graph_settings['normalize_hist']
    # calculate the labels for the data
    labels = {}
    to_v2 = {}
    from_v2 = {}
    for axis_name, (value_type, param_id) in graph_settings['axis_mapping'].items():
        axis_str = f'{axis_name}axis'
        if value_type in {'stellar', 'planet'}:
            labels[axis_str] = units_and_fields[param_id]['label']
            to_v2[param_id] = axis_str
            from_v2[axis_str] = param_id
        elif value_type == 'element':
            labels[axis_str] = f'[{param_id}/H]'
            db_field = str(param_id)
            to_v2[db_field] = axis_str
            from_v2[axis_str] = db_field
        elif value_type == 'element_ratio':
            labels[axis_str] = str(param_id)
            db_field = f'{param_id.numerator}_{param_id.denominator}'
            to_v2[db_field] = axis_str
            from_v2[axis_str] = db_field
    unique_star_names = set()
    if any([graph_settings['planet_params_returned'], graph_settings['planet_params_match_filters'], graph_settings['planet_params_value_filters']]):
        for data_row in graph_data:
            unique_star_names.add(data_row['name'])
            if 'nea_name' in data_row.keys():
                data_row['name'] = 'NEA: ' + data_row['nea_name']
    # return the data in various formats depending on the requesting application.
    if is_histogram:
        # histogram
        db_field = from_v2['xaxis']
        # value_type, param_id = axis_mapping['x']
        x_data = [db_return[db_field] for db_return in graph_data]
        x_data_with_planet = [db_return[db_field] for db_return in graph_data if 'nea_name' in db_return.keys()]
        # builds the histogram
        hist_all, edges = np.histogram(x_data, bins=20)
        hist_planet, edges = np.histogram(x_data_with_planet, bins=edges)
        # get maximum point on the histogram
        max_hist_all = float(max(hist_all))
        max_hist_planet = float(max(hist_planet))
        # normalize if necessary
        if normalize_hist:
            hist_all = hist_all / max_hist_all
            hist_planet = hist_planet / max_hist_planet
            labels['yaxis'] = 'Relative Frequency'
        else:
            labels['yaxis'] = 'Number of Stellar Systems'
        if from_api:
            return {'count': len(x_data), 'labels': labels,
                    'all_hypatia': hist_all.tolist(), 'exo_hosts': hist_planet.tolist(), 'edges': edges.tolist()}
        else:
            return {'labels': labels,
                    'hist_all': hist_all.tolist(), 'hist_planet': hist_planet.tolist(), 'edges': edges.tolist(),
                    'x_data': x_data}
    else:
        if from_api:
            return {
                'counts': len(graph_data),
                'labels': labels,
                'solarnorm': get_norm_data(solarnorm_id),
                'values': [
                    {to_v2[key] if key in to_v2.keys() else key: value for key, value in db_return.items()}
                    for db_return in graph_data
                ],
            }
        else:
            output_header = ['name'] + [f'{x_axis}axis' for x_axis in axis_mapping.keys()]
            graph_keys = [from_v2[column_name] if column_name in from_v2.keys() else column_name
                          for column_name in output_header]
            if any([planet_params_returned, planet_params_match_filters, planet_params_value_filters]):
                star_count = len(unique_star_names)
                planet_count = len(graph_data)
            else:
                star_count = len(graph_data)
                planet_count = None
            return {
                'labels': labels,
                'outputs': {data_key: data_column for data_key, data_column in zip(
                    output_header,
                    [list(i) for i in zip(*[[data_row[data_key] for data_key in graph_keys]
                                            for data_row in graph_data])],
                )},
                'star_count': star_count,
                'planet_count': planet_count,
            }


def table_query_from_request(settings: dict[str, any]):
    # parse the settings from the request for the table query
    table_settings = table_settings_from_request(settings=settings)
    return_error = table_settings['return_error']
    elements_returned = table_settings['elements_returned']
    name_types_returned = table_settings['name_types_returned']
    stellar_params_returned = table_settings['stellar_params_returned']
    planet_params_returned = table_settings['planet_params_returned']
    planet_params_match_filters = table_settings['planet_params_match_filters']
    planet_params_value_filters = table_settings['planet_params_value_filters']
    return_nea_name = bool(planet_params_returned)
    return_hover = table_settings['return_hover']
    # get the data from the database
    table_data = hypatia_db.frontend_pipeline(
        db_formatted_names=table_settings['db_formatted_names'],
        db_formatted_names_exclude=table_settings['db_formatted_names_exclude'],
        elements_match_filters=table_settings['elements_match_filters'],
        element_value_filters=table_settings['element_value_filters'],
        element_ratios_value_filters=table_settings['element_ratios_value_filters'],
        stellar_params_match_filters=table_settings['stellar_params_match_filters'],
        stellar_params_value_filters=table_settings['stellar_params_value_filters'],
        planet_params_match_filters=planet_params_match_filters,
        planet_params_value_filters=planet_params_value_filters,
        solarnorm_id=table_settings['solarnorm_id'],
        return_median=table_settings['return_median'],
        catalogs=table_settings['catalogs'],
        catalog_exclude=table_settings['catalog_exclude'],
        name_types_returned=name_types_returned,
        stellar_params_returned=stellar_params_returned,
        planet_params_returned=planet_params_returned,
        elements_returned=elements_returned,
        sort_field=table_settings['sort_field'],
        sort_reverse=table_settings['sort_reverse'],
        return_error=return_error,
        star_name_column='star_id',
        return_nea_name=return_nea_name,
        return_hover=table_settings['return_hover'],
    )

    # check the element data error values and replace them with the representative error for zero and null values
    rep_errors = [get_representative_error(el_id) for el_id in elements_returned]
    element_str_names = [str(el_id) for el_id in elements_returned]
    if return_error:
        for data_row in table_data:
            for el_name, el_rep_err in zip(element_str_names, rep_errors):
                if el_name in data_row.keys() and data_row[el_name] is not None:
                    error_name = f'{el_name}_err'
                    if error_name in data_row.keys():
                        err_value = data_row[error_name]
                        if err_value is None:
                            data_row[error_name] = el_rep_err
                        elif err_value == 0.0:
                            data_row[error_name] = el_rep_err

    # reformat the data to be a dictionary of column_name keys and list of values.
    all_columns = set()
    element_map = {}
    if elements_returned:
        element_str_names = [str(el_id) for el_id in elements_returned]
        element_map = {el_str: el_str.replace('_', '') for el_str in element_str_names}
        all_columns.update(element_str_names)
        if return_error:
            all_columns.update([f'{el_str}_err' for el_str in element_str_names])
            element_map.update({f'{el_str}_err': f'{web2py_formatted_str}_err'
                                for el_str, web2py_formatted_str in element_map.items()})
    if name_types_returned:
        all_columns.update(name_types_returned)
    if stellar_params_returned:
        all_columns.update(stellar_params_returned)
        if return_error:
            all_columns.update([f'{stellar_param}_err' for stellar_param in stellar_params_returned
                                if stellar_param not in string_names_types])
    if planet_params_returned:
        all_columns.update(planet_params_returned)
        if return_error:
            all_columns.update([f'{planet_param}_err' for planet_param in planet_params_returned
                                if planet_param not in string_names_types])
    if any([planet_params_returned, planet_params_match_filters, planet_params_value_filters]):
        all_columns.add('nea_name')
    all_columns = sorted(all_columns)
    if 'nea_name' in all_columns:
        planet_count = len(table_data)
        star_count = len(set([data_row['star_id'] for data_row in table_data]))
    else:
        planet_count = None
        star_count = len(table_data)

    hover_data = {}
    if return_hover:
        if elements_returned:
            hover_data.update({str(el_id): [] for el_id in elements_returned})
            all_element = sorted(set(elements_returned), key=element_rank)
            catalog_fields = [f'{el_id}_catalogs' for el_id in all_element]
            for data_row in table_data:
                for el_id, catalogs_field in zip(all_element, catalog_fields):
                    hover_data[str(el_id)].append(data_row.get(catalogs_field, ''))
    # return the table data
    return dict(
        body={
            column_name: data_list for column_name, data_list in
            zip(
                [element_map[col_name] if col_name in element_map.keys() else col_name for col_name in all_columns],
                zip(*[[row_data.get(col_name, '') for col_name in all_columns] for row_data in table_data])
            )
        },
        hover_data=hover_data,
        planet_count=planet_count,
        star_count=star_count,
    )


if __name__ == '__main__':
    test_settings = {
        'filter1_1': 'none',
        'filter1_2': 'H',
        'filter1_3': 'none',
        'filter1_4': 'none',
        'filter2_1': 'none',
        'filter2_2': 'H',
        'filter2_3': 'None',
        'filter2_4': 'None',
        'filter3_1': 'none',
        'filter3_2': 'H',
        'filter3_3': 'None',
        'filter3_4': 'None',
        'xaxis1': 'Fe',
        'xaxis2': 'H',
        'yaxis1': 'Si',
        'yaxis2': 'H',
        'zaxis1': 'none',
        'zaxis2': 'H',
        'cat_action': 'exclude',
        'star_action': 'exclude',
        'filter1_inv': 'False',
        'filter2_inv': 'False',
        'filter3_inv': 'False',
        'solarnorm': 'lodders09',
        'catalogs': 'luck18',
        'mode': 'scatter',
        # below are the settings for the table query
        'requested_stellar_params': '',
        'requested_elements': 'Fe;C;O;Mg;S;C;Ti;F;CII',
        'requested_planet_params': '',
        'requested_name_types': '',
        'sort': '',
        'reverse': 'true',
        'show_error': 'true',
        'show_hover': 'true',
    }
    test_graph_data = graph_query_from_request(settings=test_settings)
    # test_table_data = table_query_from_request(settings=test_settings)
