from hypatia.sources.elements import all_elements
from hypatia.sources.catalogs.solar import strip_ionization


def get_element_keys(star_dict, init_catalogs):
    catalog_names = set(star_dict.keys()) & init_catalogs
    elements_this_star = set()
    for catalog_name in catalog_names:
        for possible_element in star_dict[catalog_name].keys():
            if strip_ionization(possible_element) in all_elements:
                elements_this_star.add(possible_element)
    return elements_this_star


def core_filter(and_logic_for_lists, target_types, types_this_star):
    if and_logic_for_lists:
        # all the star types are found for this star
        if set() == target_types - types_this_star:
            return True
        else:
            return False
    else:
        # at least one of the start type are found for this star
        if set() != target_types & types_this_star:
            return True
        else:
            return False


def min_cat_count(min_cat, star_data, complement_data, init_catalogs, verbose=False):
    if min_cat is None:
        return star_data, complement_data
    else:
        if verbose:
            print("Filtering for Hypatia stars with at least", min_cat, "catalogs.")
        target_data = {star_name: star_data[star_name] for star_name in star_data.keys()
                       if len(set(star_data[star_name].keys()) & init_catalogs) >= min_cat}
        if target_data == {} and verbose:
            print("The minimum catalog count filter is returning an empty dictionary for the target data set.")
        return target_data, complement_data


def first_layer_filter(and_logic_for_lists, target_types, star_data, complement_data, verbose=False):
    if target_types is not None:
        star_names = set(star_data.keys())
        target_data = {}
        target_types = set(target_types)
        if verbose:
            if and_logic_for_lists:
                logic_str = "using 'And' logic."
            else:
                logic_str = "using 'Or' logic."
            print("Filtering in for", target_types, logic_str)
        for star_name in star_names:
            major_keys_this_star = set(star_data[star_name].keys())
            if core_filter(and_logic_for_lists, target_types, major_keys_this_star):
                target_data[star_name] = star_data[star_name]
            else:
                complement_data[star_name] = star_data[star_name]
        if target_data == {} and verbose:
            print("The first layer filter is returning an empty dictionary for the target data set.")
        return target_data, complement_data
    else:
        return star_data, complement_data


def second_layer_filter(and_logic_for_lists, target_types, star_data, complement_data, first_layer_key, verbose=False):
    if target_types is not None:
        if verbose:
            if and_logic_for_lists:
                logic_str = "using 'And' logic."
            else:
                logic_str = "using 'Or' logic."
            print("Filtering in the", first_layer_key, "dictionary for", target_types, logic_str)
        star_names = set(star_data.keys())
        target_data = {}
        target_types = set(target_types)
        for star_name in star_names:
            if first_layer_key in set(star_data[star_name].keys()):
                name_types_this_star = set(star_data[star_name][first_layer_key].keys())
                if core_filter(and_logic_for_lists, target_types, name_types_this_star):
                    target_data[star_name] = star_data[star_name]
                else:
                    complement_data[star_name] = star_data[star_name]
            else:
                complement_data[star_name] = star_data[star_name]
        if target_data == {} and verbose:
            print("The second layer filter is returning an empty dictionary for the target data set.")
        return target_data, complement_data
    else:
        return star_data, complement_data


def second_layer_bound_filter(targets, star_data, complement_data, first_layer_key, verbose=False):
    if targets is None:
        return star_data, complement_data
    else:
        target_types = [target for target, lower_bound, upper_bound in targets]
        # filter the data to have all the required target types.
        star_data, complement_data = second_layer_filter(True, target_types, star_data, complement_data, first_layer_key)
        # filter the data again to make sure all the data is in the bounds
        star_names = set(star_data.keys())
        target_data = {}
        for target, lower_bound, upper_bound in targets:
            if verbose:
                print("Bound filtering in the", first_layer_key, "dictionary")
                print("  for the parameter", target, "for a lower bound of", lower_bound, "and an upper bound of",
                      upper_bound, ".")
            for star_name in star_names:
                below_upper = True
                if upper_bound is not None:
                    if star_data[star_name][first_layer_key][target] >= upper_bound:
                        below_upper = False
                above_lower = True
                if lower_bound is not None:
                    if star_data[star_name][first_layer_key][target] < lower_bound:
                        above_lower = False
                if above_lower and below_upper:
                    target_data[star_name] = star_data[star_name]
                else:
                    complement_data[star_name] = star_data[star_name]
        if target_data == {} and verbose:
            print("The second layer bound filter is returning an empty dictionary for the target data set.")
        return target_data, complement_data


def second_layer_match_filter(targets, star_data, complement_data, first_layer_key, verbose=False):
    if targets is None:
        return star_data, complement_data
    else:
        target_types = [target for target, match_values in targets]
        # filter the data to have all the required target types.
        star_data, complement_data = second_layer_filter(True, target_types, star_data, complement_data,
                                                         first_layer_key)
        # filter the data again to make sure all the data is in the bounds
        star_names = set(star_data.keys())
        target_data = {}
        for target, match_values in targets:
            if verbose:
                print("Match filtering in the", first_layer_key, "dictionary")
                print("  for the parameter", target, "target values of", match_values, ".")
            for star_name in star_names:
                if target == "SpType":
                    value = star_data[star_name][first_layer_key][target][0]
                else:
                    value = star_data[star_name][first_layer_key][target]
                if value in match_values:
                    target_data[star_name] = star_data[star_name]
                else:
                    complement_data[star_name] = star_data[star_name]
        if target_data == {} and verbose:
            print("The second layer match filter is returning an empty dictionary for the target data set.")
        return target_data, complement_data


def elements_filter(and_logic_for_lists, target_types, star_data, complement_data, init_catalogs, verbose=False):
    if target_types is not None:
        if verbose:
            if and_logic_for_lists:
                logic_str = "using 'And' logic."
            else:
                logic_str = "using 'Or' logic."
            print("Filtering by the elements:", target_types, logic_str)
        star_names = set(star_data.keys())
        target_data = {}
        target_types = set(target_types)
        for star_name in star_names:
            elements_this_star = get_element_keys(star_data[star_name], init_catalogs)
            if core_filter(and_logic_for_lists, target_types, elements_this_star):
                target_data[star_name] = star_data[star_name]
            else:
                complement_data[star_name] = star_data[star_name]
        if target_data == {} and verbose:
            print("The element filter is returning an empty dictionary for the target data set.")
        return target_data, complement_data
    else:
        return star_data, complement_data
