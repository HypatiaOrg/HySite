import re
import random

import numpy as np

from api.db import summary_doc, hypatia_db
from hypatia.legacy.data_formats import legacy_float
from hypatia.elements import ElementID, RatioID, hydrogen_id
from api.v2.data_process import (get_norm_key, get_norm_data, get_catalog_summary, total_stars, total_abundance_count,
                                 available_wds_stars, available_nea_names, available_elements_v2, available_catalogs_v2,
                                 normalizations_v2)


stellar_param_types_v2 = ['raj2000', 'decj2000', 'dist', 'x_pos', 'y_pos', 'z_pos', 'teff', 'logg',
                          'sptype', 'vmag', 'bmag', 'bv', 'pm_ra', 'pm_dec', 'u_vel', 'v_vel', 'w_vel',
                          'disk', 'mass', 'rad']
stellar_param_types_v2_set = set(stellar_param_types_v2)
planet_param_types_v2 = ["semi_major_axis", "eccentricity", "inclination", "pl_mass", "pl_radius"]
planet_param_types_v2_set = set(planet_param_types_v2)
ranked_string_params = {'sptype': 'sptype_num', 'disk': 'disk_num'}
nones = {None, 'none', ''}
none_denominators = {None, 'none', '', 'h', 'H'}

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
        'plusminus': ref_this_el['plusminus'],
        'element_name': element_name,
        'abbreviation': abbreviation,
    })


def check_filter(x, test_filter) -> bool:
    if test_filter[2]:
        return not check_filter(x, (test_filter[0], test_filter[1], False))
    if test_filter[0] is not None and filter[1] is not None:
        return (test_filter[0] <= x) and (x <= test_filter[1])
    elif test_filter[0] is not None:
        return test_filter[0] <= x
    elif test_filter[1] is not None:
        return x <= test_filter[1]
    else:
        return True


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
        # ensure the types are of the filter_low and filter_high are either float or None
        if filter_low is not None and filter_high is not None:
            filter_low = float(filter_low)
            filter_high = float(filter_high)
            if filter_low > filter_high:
                filter_low, filter_high = filter_high, filter_low
        elif filter_low is not None:
            filter_low = float(filter_low)
        elif filter_high is not None:
            filter_high = float(filter_high)
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


def graph_query(
        xaxis1: str, xaxis2: str | None = None,
        yaxis1: str | None = None, yaxis2: str | None = None,
        zaxis1: str | None = None, zaxis2: str | None = None,
        filter1_1: str | None = None, filter1_2: str | None = None,
        filter1_3: float | None = None, filter1_4: float | None = None, filter1_inv: bool = False,
        filter2_1: str | None = None, filter2_2: str | None = None,
        filter2_3: float | None = None, filter2_4: float | None = None, filter2_inv: bool = False,
        filter3_1: str | None = None, filter3_2: str | None = None,
        filter3_3: float | None = None, filter3_4: float | None = None, filter3_inv: bool = False,
        cat_action: str = 'exclude', catalogs: set[str] | None = None,
        star_action: str = 'exclude', star_list: list[str] | None = None,
        solarnorm_id: str = 'absolute', return_median: bool = True,
        mode: str = 'scatter',
        normalize_hist: bool = False,
    ) -> dict[str, any]:
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

    # get compositions
    graph_data = hypatia_db.graph_data_v2(
        db_formatted_names=db_formatted_names,
        db_formatted_names_exclude=star_action == "exclude",
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
        solarnorm_id=get_norm_key(solarnorm_id),
        return_median=return_median,
        catalogs=catalogs,
        catalog_exclude=cat_action == "exclude",
    )
    labels = {}
    to_v2 = {}
    from_v2 = {}
    for axis_name, (value_type, param_id) in axis_mapping.items():
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
    if mode == 'scatter':
        return {
            'values': [
                {to_v2[key] if key in to_v2.keys() else key: value for key, value in db_return.items()}
                for db_return in graph_data],
            'solarnorm': get_norm_data(solarnorm_id),
            'counts': len(graph_data),
            'labels': labels,
        }
    else:
        # histogram
        # labels = {}

        db_field = from_v2['xaxis']
        # value_type, param_id = axis_mapping['x']
        x_data = [db_return[db_field] for db_return in graph_data]







        # # counts stars with planets
        # with_planet = []
        # for i in range(len(outputs['xaxis'])):
        #     getstarid = outputs['hip'][i]
        #     try:
        #         getstarid = re.sub("[^0-9]", "", getstarid)
        #     except:
        #         pass
        #     starid = hashTable['starid-%s' % getstarid][0]
        #     if ("planet-%s-b" % starid) in hashTable:
        #         with_planet.append(outputs['xaxis'][i])
        # # builds the histogram
        # hist_all, edges = np.histogram(outputs['xaxis'], bins=20)
        # hist_planet, edges = np.histogram(with_planet, bins=edges)
        # # get maximum point on the histogram
        # max_hist_all = float(max(hist_all))
        # max_hist_planet = float(max(hist_planet))
        # # normalize if necessary
        # if normalize_hist:
        #     hist_all = hist_all / max_hist_all
        #     hist_planet = hist_planet / max_hist_planet
        #     max_hist_all = 1
        #     max_hist_planet = 1
        #     labels['yaxis'] = "Relative Frequency"
        #     fill_alpha = 0.5
        #     line_alpha = 0.2
        # else:
        #     labels['yaxis'] = 'Number of Stellar Systems'
        #     fill_alpha = 1
        #     line_alpha = 1
        # return {"all_hypatia": hist_all.tolist(), "exo_hosts": hist_planet.tolist(), "edges": edges.tolist(),
        #           "labels": labels, "count": len(outputs['xaxis'])}
        return {"x_data": x_data}


def graph_query_from_request(settings: dict[str, any]) -> dict[str, any]:
    filter1_1 = settings.get('filter1_1', 'none')
    filter1_2 = settings.get('filter1_2', 'H')
    filter1_3 = legacy_float(settings.get('filter1_3', None))
    filter1_4 = legacy_float(settings.get('filter1_4', None))
    filter2_1 = settings.get('filter2_1', 'none')
    filter2_2 = settings.get('filter2_2', 'H')
    filter2_3 = legacy_float(settings.get('filter2_3', None))
    filter2_4 = legacy_float(settings.get('filter2_4', None))
    filter3_1 = settings.get('filter3_1', 'none')
    filter3_2 = settings.get('filter3_2', 'H')
    filter3_3 = legacy_float(settings.get('filter3_3', None))
    filter3_4 = legacy_float(settings.get('filter3_4', None))
    xaxis1 = settings.get('xaxis1', 'Fe')
    xaxis2 = settings.get('xaxis2', 'H')
    yaxis1 = settings.get('yaxis1', 'Si')
    yaxis2 = settings.get('yaxis2', 'H')
    zaxis1 = settings.get('zaxis1', 'none')
    zaxis2 = settings.get('zaxis2', 'H')
    cat_action = settings.get('cat_action', 'exclude')
    star_action = settings.get('star_action', 'include')
    filter1_inv = bool(settings.get('filter1_inv', False))
    filter2_inv = bool(settings.get('filter2_inv', False))
    filter3_inv = bool(settings.get('filter3_inv', False))
    solarnorm_id = get_norm_key(settings.get('solarnorm', 'lodders09'))
    normalize = bool(settings.get('normalize', False))
    if solarnorm_id is None:
        solarnorm_id = 'lodders09'
    catalogs = sorted({cat_data['id'] for cat_data
                      in [get_catalog_summary(raw_name) for raw_name in settings.get('catalogs', [])]
                      if cat_data is not None})
    mode = settings.get('mode', None)
    if mode != "hist":
        mode = "scatter"
    return graph_query(filter1_1=filter1_1, filter1_2=filter1_2, filter1_3=filter1_3, filter1_4=filter1_4,
                       filter2_1=filter2_1, filter2_2=filter2_2, filter2_3=filter2_3, filter2_4=filter2_4,
                       filter3_1=filter3_1, filter3_2=filter3_2, filter3_3=filter3_3, filter3_4=filter3_4,
                       xaxis1=xaxis1, xaxis2=xaxis2, yaxis1=yaxis1, yaxis2=yaxis2, zaxis1=zaxis1, zaxis2=zaxis2,
                       cat_action=cat_action, star_action=star_action,
                       filter1_inv=filter1_inv, filter2_inv=filter2_inv, filter3_inv=filter3_inv,
                       solarnorm_id=solarnorm_id, catalogs=set(catalogs), mode=mode, normalize_hist=normalize)


if __name__ == '__main__':
    test_settings = {
        'filter1_1': 'none',
        'filter1_2': 'H',
        'filter1_3': None,
        'filter1_4': None,
        'filter2_1': 'none',
        'filter2_2': 'H',
        'filter2_3': None,
        'filter2_4': None,
        'filter3_1': 'none',
        'filter3_2': 'H',
        'filter3_3': None,
        'filter3_4': None,
        'xaxis1': 'Fe',
        'xaxis2': 'H',
        'yaxis1': 'Si',
        'yaxis2': 'H',
        'zaxis1': 'none',
        'zaxis2': 'H',
        'cat_action': 'exclude',
        'star_action': 'include',
        'filter1_inv': False,
        'filter2_inv': False,
        'filter3_inv': False,
        'solarnorm': 'lodders09',
        'catalogs': [],
        'mode': 'scatter',
    }
    graph_data = graph_query_from_request(settings=test_settings)