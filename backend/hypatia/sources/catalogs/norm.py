# This the dictionary that stores the normalization functions
un_norm_functions = {}


# This is the decorator function that assigns the un-normalization functions to a dictionary at import time
def un_norm_func(func):
    name_type = func.__name__
    un_norm_functions[name_type] = func
    return func


@un_norm_func
def un_norm_x_over_h(relative_x_over_h, solar_x):
    """
    We take the relative value of an element X to Hydrogen (H) of a star compared to the solar abundance of the same
    ratio. Note that this calculation takes place in Log base 10 space, and returns values in log space, so simple
    additions and subtractions are all that is needed for this calculation.

    The abundance of Hydrogen, H_star, is defined as 10^12 atoms thus log(H_star) = log(10^12) = 12. By this definition,
    H_solar := log(10^12) = 12 and H_star := log(10^12) = 12 thus H_star = H_solar

    All other abundances are compared to that value. For a given elements X if may hav 10^6 atoms per 10^12 hydrogen
    atoms. Thus, the absolute abundance of element X is reported as log(X_star) = log(10^6) = 6. Since Hydrogen is the
    most abundant element for any star each the reported elemental abundance will be in the range of
    [12, -inf] = [log(10^12), log(0)].

    :param relative_x_over_h: is equal to log(X_star / H_star) - log(X_solar / H_solar)
                                        = log(X_star) - log(H_star) - log(X_solar) + log(H_solar)
        but since H_solar = H_star by definitions we have:
                      relative_x_over_h = log(X_star) - log(X_solar)
    :param solar_x: id equal to log(X_solar)
    :return: log(X_star) = relative_x_over_h + log(solar) = log(X_star) - log(X_solar) + log(X_solar)
    """
    return relative_x_over_h + solar_x


@un_norm_func
def un_norm_x_over_fe(relative_x_over_fe, relative_fe_over_h, solar_x):
    """
    We take the relative value of an element X to Iron (Fe) of a star compared to the solar abundance of the same
    ratio. Note the this calculation takes place in Log base 10 space, and returns values in log space, so simple
    additions and subtractions are all that is needed for this calculation.

    The abundance of Hydrogen, H_star, is defined as 10^12 atoms thus log(H_star) = log(10^12) = 12. By this definition,
    H_solar := log(10^12) = 12 and H_star := log(10^12) = 12 thus H_star = H_solar

    All other abundances are compared to that value. For a given elements X if may hav 10^6 atoms per 10^12 hydrogen
    atoms. Thus, the absolute abundance of element X is reported as log(X_star) = log(10^6) = 6. Since Hydrogen is the
    most abundant element for any star each the reported elemental abundance will be in the range of
    [12, -inf] = [log(10^12), log(0)].

    We calculate the intermediate product log(X_relative / H_relative) = log(X_star / H_star) - log(X_solar / H_solar)
    as: relative_x_over_fe + relative_fe_over_h = log(X_relative / Fe_relative) + log(Fe_relative / H_relative)
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star / Fe_star) - log(X_solar / Fe_solar)
                                                        + log(Fe_star/ H_star) - log(Fe_solar / H_solar)
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star * Fe_solar / (Fe_star * X_solar))
                                                        + log(Fe_star * H_solar / (H_star * Fe_solar))
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star * Fe_solar * Fe_star * H_solar
                                                        / (Fe_star * X_solar * H_star * Fe_solar))
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star * H_solar / (X_solar * H_star))
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star / H_star) - log(X_solar / H_solar)
    <=> relative_x_over_fe + relative_fe_over_h = log(X_relative / H_relative)
    which we name relative_x_over_h as log(X_relative / H_relative) = relative_x_over_fe + relative_fe_over_h

    At this point we have the case that handled by the function un_norm_x_over_h defined above to return the
    desired log(X_star / H_star) = un_norm_x_over_h(relative_x_over_h, solar_x_over_h)

    :param relative_x_over_fe: log(X_relative / Fe_relative) = log(X_star / Fe_star) - log(X_solar / Fe_solar)
    :param relative_fe_over_h: log(Fe_relative / H_relative) = log(Fe_star/ H_star) - log(Fe_solar / H_solar)
    :param solar_x: log(X_solar)
    :return: log(X_star)
    """
    relative_x_over_h = relative_x_over_fe + relative_fe_over_h
    return un_norm_x_over_h(relative_x_over_h, solar_x)


@un_norm_func
def un_norm_abs_x(absolute_x):
    """
    Absolute data is already in the desired standard. Nothing is is done here for to un normalize the data.

    The abundance of Hydrogen, H_star, is defined as 10^12 atoms thus log(H_star) = log(10^12) = 12. By this definition,
    H_solar := log(10^12) = 12 and H_star := log(10^12) = 12 thus H_star = H_solar

    All other abundances are compared to that value. For a given elements X if may hav 10^6 atoms per 10^12 hydrogen
    atoms. Thus, the absolute abundance of element X is reported as log(X_star) = log(10^6) = 6. Since Hydrogen is the
    most abundant element for any star each the reported elemental abundance will be in the range of
    [12, -inf] = [log(10^12), log(0)].

    :param absolute_x: is equal to log(X_star)
    :return: absolute_x = log(X_star)
    """
    return absolute_x


def strip_ionization(test_string):
    if len(test_string) < 2:
        return test_string
    elif test_string[1].isupper():
        return test_string[0]
    else:
        return test_string[0:2]


def ratio_to_element(test_ratio):
    if "NLTE" in test_ratio:
        NLTE_flag = True
        test_ratio = test_ratio.replace("NLTE", "").strip("_").strip()
    else:
        NLTE_flag = False
    test_ratio = test_ratio.strip()
    if test_ratio[0] == "A" and test_ratio[1].isupper():
        # the case that this is an absolute abundance is being reported
        element_string = test_ratio[1:]
        un_norm_func_name = "un_norm_abs_x"
    elif test_ratio in element_abrevs:
        element_string = test_ratio
        un_norm_func_name = "un_norm_x_over_h"
    elif test_ratio[-1] == "H":
        # This is the case when the reported abundance is a ratio of the element value to the value of Hydrogen
        element_string = test_ratio[:-1]
        un_norm_func_name = "un_norm_x_over_h"
    elif test_ratio[-2:] == "Fe":
        # This is the case when the reported abundance is a ratio of the element value to the value of Iron
        element_string = test_ratio[:-2]
        un_norm_func_name = "un_norm_x_over_fe"
    else:
        raise KeyError("The Abundance: " + str(test_ratio) + " is not of the expected formats.")
    if element_string[-1] == "I" and len(element_string) > 1 and element_string[-2].islower():
        # The case where a neutral element is suffixed with an "I" as in FeI instead of Fe
        element_string = element_string[:-1]
    if NLTE_flag:
        element_string += "_NLTE"
    return element_string, un_norm_func_name


def un_norm(element_dict, norm_dict):
    un_norm_dict = {}
    key_set = set(element_dict.keys())
    for test_ratio in key_set:
        element_string, un_norm_func_name = ratio_to_element(test_ratio)
        if un_norm_func_name == "un_norm_x_over_fe":
            if "FeH" in key_set:
                iron_ratio_string = "FeH"
            elif "FeIH" in key_set:
                iron_ratio_string = "FeIH"
            elif "AFe" in key_set:
                element_dict["FeH"] = element_dict["AFe"] - norm_dict["Fe"]
                iron_ratio_string = "FeH"
            else:
                raise NameError("The required Fe/H ratio (or AFe and solar norm value for Fe) is not found,\n" +
                                "using the keys FeH or FeIH.")
            if element_string in norm_dict.keys():
                un_norm_dict[element_string] = un_norm_functions[un_norm_func_name](element_dict[test_ratio],
                                                                                    element_dict[iron_ratio_string],
                                                                                    norm_dict[element_string])
        elif un_norm_func_name == "un_norm_x_over_h":
            if element_string in norm_dict.keys():
                un_norm_dict[element_string] = un_norm_functions[un_norm_func_name](element_dict[test_ratio],
                                                                                    norm_dict[element_string])
        else:
            un_norm_dict[element_string] = un_norm_functions[un_norm_func_name](element_dict[test_ratio])
    return un_norm_dict