import re
import random

import numpy as np

from api.db import summary_doc
from hypatia.elements import ElementID, hydrogen_id
from hypatia.legacy.data_formats import legacy_float, legacy_spectype
from api.v2.data_process import (get_norm_key, get_norm_data, get_catalog_summary, total_stars, total_abundance_count,
                                 available_wds_stars, available_nea_names, available_elements_v2, available_catalogs_v2,
                                 normalizations_v2)


stellar_param_types_v2 = ['raj2000', 'decj2000', 'dist', 'x_pos', 'y_pos', 'z_pos', 'teff', 'logg',
                          'sptype', 'vmag', 'bmag', 'bv', 'pm_ra', 'pm_dec', 'u_vel', 'v_vel', 'w_vel',
                          'disk', 'mass', 'rad']
planet_param_types_v2 = ["semi_major_axis", "eccentricity", "inclination", "pl_mass", "pl_radius"]
ranked_string_params = {'sptype': 'sptype_num', 'disk': 'disk_num'}

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


def plot_query(filter1_1: str, filter1_2: str, filter1_3: float | None, filter1_4: float | None,
               filter2_1: str, filter2_2: str, filter2_3: float | None, filter2_4: float | None,
               filter3_1: str, filter3_2: str, filter3_3: float | None, filter3_4: float | None,
               filter1_inv: bool, filter2_inv: bool, filter3_inv: bool,
               mode: str, xaxis1: str, xaxis2: str, yaxis1: str, yaxis2: str, zaxis1: str, zaxis2: str,
               cat_action: str, catalogs: list[str] | None,
               star_action: str, star_list: list[str] | None,
               solarnorm_id: str, normalize: bool
               ) -> dict[str, any]:
    result = {}

    # define variables
    elements = {}
    stellarProps = {}
    planetProps = {}
    filters = {}
    planetFilters = {}

    # which axes are needed?
    # histogram: X only
    # scatter: X, Y
    # scatter with color: X, Y, Z
    axes = [('xaxis', xaxis1, xaxis2)]
    if mode == "scatter":
        axes.append(('yaxis', yaxis1, yaxis2))
        if zaxis1 != "none":
            axes.append(('zaxis', zaxis1, zaxis2))

    # filter the data
    if filter1_1 != "none" and (filter1_3 is not None or filter1_4 is not None):
        axes.append(('filter1_', filter1_1, filter1_2))
        if filter1_1 in planet_param_types:
            planetFilters['filter1_'] = (filter1_3, filter1_4, filter1_inv)
        else:
            filters['filter1_'] = (filter1_3, filter1_4, filter1_inv)
    if filter2_1 != "none" and (filter2_3 is not None or filter2_4 is not None):
        axes.append(('filter2_', filter2_1, filter2_2))
        if filter2_1 in planet_param_types:
            planetFilters['filter2_'] = (filter2_3, filter2_4, filter2_inv)
        else:
            filters['filter2_'] = (filter2_3, filter2_4, filter2_inv)
    if filter3_1 != "none" and (filter3_3 is not None or filter3_4 is not None):
        axes.append(('filter3_', filter3_1, filter3_2))
        if filter3_1 in planet_param_types:
            planetFilters['filter3_'] = (filter3_3, filter3_4, filter3_inv)
        else:
            filters['filter3_'] = (filter3_3, filter3_4, filter3_inv)

    # parse the data types from the axis
    for axis_name, first_val, second_val in axes:
        if first_val in stellar_param_types:
            stellarProps[axis_name] = first_val
        elif first_val in planet_param_types:
            planetProps[axis_name] = first_val
        else:
            elements[axis_name + "1"] = ElementID.from_str(first_val)
            denominator_element = ElementID.from_str(second_val)
            if denominator_element != hydrogen_id:
                elements[axis_name + "2"] = denominator_element



    # get compositions
    compositions = pd.read_hdf(os.path.join(HYP_DATA_DIR, "compositions.%s.h5" % solarnorm_id), "compositions")

    # include/exclude catalogs
    if catalogs:
        if cat_action == "exclude":
            compositions = compositions[~compositions.catalogue.isin(catalogs)]
        elif catalogs:
            compositions = compositions[compositions.catalogue.isin(catalogs)]

    # include/exclude stars
    if star_list:
        if star_action == "exclude":
            compositions = compositions[~compositions.star_hip.isin(hipData)]
        else:
            compositions = compositions[compositions.star_hip.isin(hipData)]

    # get all the hips
    stars = db(db.t_star.id > 0).select(db.t_star.f_hip)
    hips = [star.f_hip for star in stars]

    # get planet/stellar properties
    hashTable = PersistentDict(os.path.join(HYP_DATA_DIR, "hashtable.shelf"))

    # get compositions relevant to scatter plot
    xy_data = compositions[compositions.element.isin(list(elements.values()))]

    # add abundances
    myStars = Stars()
    for abundance in xy_data.itertuples():
        myStars.addAbundance(abundance.star_hip, abundance.element, abundance.value)

    # generate outputs
    outputs = {axis_name: [] for axis_name, first_val, second_val in axes} | {'hip': [], 'name': []}
    value = {}
    for hip in hips:
        for axis_name, first_val, second_val in axes:
            item_one_name = axis_name + "1"
            item_two_name = axis_name + "2"
            if axis_name in planetProps:  # planet parameter
                value[axis_name] = random.randint(9000, 9999)  # we'll fill this out later
                continue
            if axis_name in stellarProps:  # stellar parameter
                test_val = hashTable['star-%s' % hip].get("f_" + stellarProps[item])
                if test_val == 9999:
                    test_val = None
                elif test_val == "thin":
                    test_val = 0
                elif test_val == "thick":
                    test_val = 1
                elif test_val == "N/A":
                    test_val = None
                elif stellarProps[axis_name] == "spec":
                    value[axis_name] = legacy_spectype(test_val)
                value[axis_name] = test_val
                continue
            value[axis_name] = myStars.getStatistic(hip, elements[item_one_name])  # element ratio
            if value[axis_name] is None:
                continue
            if item_one_name in elements:  # denominator is not H
                value2 = myStars.getStatistic(hip, elements[item_two_name])
                if value2 is None:
                    value[axis_name] = None
                    continue
                value[axis_name] -= value2
        # only plot if there is a value for each axis and it matches the filter
        if (all([value[axis_name] is not None for axis_name, first_val, second_val in axes])
                and all([check_filter(value[f], filters[f]) for f in filters])):
            for axis_name, first_val, second_val in axes:
                outputs[axis_name].append(value[axis_name])
            outputs['hip'].append(hip)
            outputs['name'].append(hashTable['star-%s' % hip].get("f_preferred_name"))

    # if there are any planet parameters, then each data point should be
    # a planet as opposed to a star. Start the process again
    if len(planetProps) > 0:
        planet_outputs = {axis_name: [] for axis_name, first_val, second_val in axes}
        planet_outputs['hip'] = []
        value = {}
        hiplist = []
        for i in range(len(outputs['hip'])):
            starid = hashTable['starid-%s' % outputs['hip'][i]][0]
            for char in "bcdefghijklmnopqrstuvwxyz":
                if "planetid-%s-%s" % (starid, char) not in hashTable:
                    break
                for axis_name, first_val, second_val in axes:
                    if axis_name in planetProps:  # planet parameter
                        test_value = hashTable['planetid-%s-%s' % (starid, char)].get("f_" + planetProps[axis_name])
                        if test_value == 999:
                            test_value = None
                        value[axis_name] = test_value
                    else:  # leftover stellar parameter or element ratio
                        value[axis_name] = outputs[axis_name][i]
                # only plot if there is a value for each axis and it matches the filter
                if (all([value[axis_name] for axis_name, first_val, second_val in axes])
                        and all([check_filter(value[f], planetFilters[f]) for f in planetFilters])):
                    for axis_name, first_val, second_val in axes:
                        planet_outputs[axis_name].append(value[axis_name])
                    planet_outputs['hip'].append(str(outputs['hip'][i]) + char)
                    hiplist.append(outputs['hip'][i])
        outputs = planet_outputs
    else:
        hiplist = outputs['hip']

    # build the plot
    TOOLS = "crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,"

    # build the labels
    labels = {}
    unique_labels = {}
    for axis_name, first_val, second_val in axes:
        if axis_name in stellarProps:
            labels[axis_name] = first_val
        elif axis_name in planetProps:
            labels[axis_name] = first_val
        else:
            labels[axis_name] = f"[{first_val}/{second_val}]"
        if labels[axis_name] not in list(unique_labels.values()):
            unique_labels[axis_name] = labels[axis_name]

    # if there is no data then return a message
    if len(outputs['xaxis']) == 0:
        result = {"count": 0}

    # histogram
    elif mode == "hist":
        # counts stars with planets
        with_planet = []
        for i in range(len(outputs['xaxis'])):
            getstarid = outputs['hip'][i]
            try:
                getstarid = re.sub("[^0-9]", "", getstarid)
            except:
                pass
            starid = hashTable['starid-%s' % getstarid][0]
            if ("planet-%s-b" % starid) in hashTable:
                with_planet.append(outputs['xaxis'][i])
        # builds the histogram
        hist_all, edges = np.histogram(outputs['xaxis'], bins=20)
        hist_planet, edges = np.histogram(with_planet, bins=edges)
        # get maximum point on the histogram
        max_hist_all = float(max(hist_all))
        max_hist_planet = float(max(hist_planet))
        # normalize if necessary
        if normalize:
            hist_all = hist_all / max_hist_all
            hist_planet = hist_planet / max_hist_planet
            max_hist_all = 1
            max_hist_planet = 1
            labels['yaxis'] = "Relative Frequency"
            fill_alpha = 0.5
            line_alpha = 0.2
        else:
            labels['yaxis'] = 'Number of Stellar Systems'
            fill_alpha = 1
            line_alpha = 1
        result = {"all_hypatia": hist_all.tolist(), "exo_hosts": hist_planet.tolist(), "edges": edges.tolist(),
                  "labels": labels, "count": len(outputs['xaxis'])}
    else:  # Scatter
        for i in range(len(outputs['hip'])):
            point = {}
            for col in outputs:
                point[col.replace("_", "")] = outputs[col][i]
            result.append(point)
        for col in labels:
            if "_" in col:
                labels[col.replace("_", "")] = labels[col]
                del (labels[col])
        result = {"values": result, "labels": labels, "count": len(outputs['xaxis'])}
        for item in result['values']:
            del (item['hip'])
    result['solarnorm'] = get_norm_data(solarnorm_id)
    return result


def from_legacy(request):
    inputs = dict(request.vars)
    filter1_1 = inputs.get('filter1_1', 'none')
    filter1_2 = inputs.get('filter1_2', 'H')
    filter1_3 = legacy_float(inputs.get('filter1_3', None))
    filter1_4 = legacy_float(inputs.get('filter1_4', None))
    filter2_1 = inputs.get('filter2_1', 'none')
    filter2_2 = inputs.get('filter2_2', 'H')
    filter2_3 = legacy_float(inputs.get('filter2_3', None))
    filter2_4 = legacy_float(inputs.get('filter2_4', None))
    filter3_1 = inputs.get('filter3_1', 'none')
    filter3_2 = inputs.get('filter3_2', 'H')
    filter3_3 = legacy_float(inputs.get('filter3_3', None))
    filter3_4 = legacy_float(inputs.get('filter3_4', None))
    xaxis1 = inputs.get('xaxis1', 'Fe')
    xaxis2 = inputs.get('xaxis2', 'H')
    yaxis1 = inputs.get('yaxis1', 'Si')
    yaxis2 = inputs.get('yaxis2', 'H')
    zaxis1 = inputs.get('zaxis1', 'none')
    zaxis2 = inputs.get('zaxis2', 'H')
    cat_action = inputs.get('cat_action', 'exclude')
    star_action = inputs.get('star_action', 'include')
    filter1_inv = bool(inputs.get('filter1_inv', False))
    filter2_inv = bool(inputs.get('filter2_inv', False))
    filter3_inv = bool(inputs.get('filter3_inv', False))
    solarnorm_id = get_norm_key(inputs.get('solarnorm', 'lodders09'))
    if solarnorm_id is None:
        solarnorm_id = 'lodders09'
    normalize = solarnorm_id in {'absolute', 'original'}
    catalogs = sorted({cat_data['id'] for cat_data
                      in [get_catalog_summary(raw_name) for raw_name in inputs.get('catalogs', [])]
                      if cat_data is not None})
    mode = inputs.get('mode', None)
    if mode != "hist":
        mode = "scatter"
    return plot_query(filter1_1=filter1_1, filter1_2=filter1_2, filter1_3=filter1_3, filter1_4=filter1_4,
                      filter2_1=filter2_1, filter2_2=filter2_2, filter2_3=filter2_3, filter2_4=filter2_4,
                      filter3_1=filter3_1, filter3_2=filter3_2, filter3_3=filter3_3, filter3_4=filter3_4,
                      xaxis1=xaxis1, xaxis2=xaxis2, yaxis1=yaxis1, yaxis2=yaxis2, zaxis1=zaxis1, zaxis2=zaxis2,
                      cat_action=cat_action, star_action=star_action,
                      filter1_inv=filter1_inv, filter2_inv=filter2_inv, filter3_inv=filter3_inv,
                      solarnorm_id=solarnorm_id, normalize=normalize, catalogs=catalogs, mode=mode)