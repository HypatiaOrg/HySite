import os
import datetime

from hypatia.config import working_dir

now = datetime.datetime.now()
day = '%02i' % now.day
month = '%02i' % now.month
year = '%04i' % now.year
legacy_file_name = os.path.join(working_dir, "load", "data_products",
                                F"Petigura_11_14_10_19_Lodders09.txt")
new_file_name = os.path.join(working_dir, "load", "data_products",
                             F"hypatia_{day}_{month}_{year}_normLodders09.txt")
star_params = ['hd', "bd", '2MASS', "dist (pc)", "RA", "Dec", "RA proper motion", "Dec proper motion", "Position",
               "UVW", "Disk component", "Spec Type", "Teff", "logg", "Vmag", "Bmag", "B-V"]


def number_format(num):
    if num == "nan":
        num = ""
    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            return num


def sort_old_hypatia_output():
    file_name = os.path.join(working_dir, "load", "data_products", "Caleb_hypatia_norm_9_08_19_Lodders09.txt")
    new_file_name = file_name[:-4] + "_remix.txt"
    with open(file_name, "r") as of:
        contents = of.read().split("\n\n")
    star_text_dict = {}
    for star_text in contents:
        if star_text != '':
            first_line, *_ = star_text.split('\n', 1)
            hip_name = float(first_line[12:])
            star_text_dict[hip_name] = star_text
    hip_names = sorted(star_text_dict.keys())
    with open(new_file_name, 'w') as nf:
        for hip_name in hip_names:
            nf.write(star_text_dict[hip_name] + '\n\n')
        nf.write("\n")
    return


def load_from_text(file_name):
    with open(file_name, "r") as f:
        contents = f.read().split("\n\n")
    star_text_dict = {}
    for star_text in contents:
        if star_text != '':
            lines_for_this_star = star_text.split('\n')
            hip_name = lines_for_this_star[0][12:]
            star_text_dict[hip_name] = {}
            for index, star_param in list(enumerate(star_params)):
                if star_param == "Disk component":
                    replace_str = "Disk component: "
                else:
                    replace_str = star_param + " = "
                formatted_value = number_format(lines_for_this_star[1 + index].replace(replace_str, "").strip())
                star_text_dict[hip_name][star_param] = formatted_value

            if star_text_dict[hip_name]['bd'] != "":
                a, b = star_text_dict[hip_name]['bd'].replace("B", "").replace("   ", " ").replace("  ", " ").split(" ")
                star_text_dict[hip_name]['bd'] = (number_format(a), number_format(b))
            if star_text_dict[hip_name]['Position'] != "":
                a, b, c = star_text_dict[hip_name]['Position'].replace("[", "").replace("]", "").split(", ")
                star_text_dict[hip_name]['Position'] = (number_format(a), number_format(b), number_format(c))
            if star_text_dict[hip_name]['UVW'] != "":
                a, b, c = star_text_dict[hip_name]['UVW'].replace("(", "").replace(")", "").split(", ")
                star_text_dict[hip_name]['UVW'] = (number_format(a), number_format(b), number_format(c))

            catalogs_this_star = set()
            for element_index in range(len(star_params) + 1, len(lines_for_this_star)):
                if "(NLTE)" in lines_for_this_star[element_index]:
                    element, _, value, catalog = lines_for_this_star[element_index].split(" ", 3)
                    element += "_NLTE"
                else:
                    element, value, catalog = lines_for_this_star[element_index].split(" ", 2)
                if catalog not in catalogs_this_star:
                    catalogs_this_star.add(catalog)
                    star_text_dict[hip_name][catalog] = {}
                if element in star_text_dict[hip_name][catalog].keys():
                    existing_data = star_text_dict[hip_name][catalog][element]
                    if type(existing_data) == float:
                        temp_list = [existing_data]
                    else:
                        temp_list = list(existing_data)
                    temp_list.append(float(value))
                    star_text_dict[hip_name][catalog][element] = tuple(sorted(temp_list))
                else:
                    star_text_dict[hip_name][catalog][element] = float(value)
    return star_text_dict


def extra_stars(extra_names, in_name, out_name, in_star_dict, star_to_ignore=set()):
    if extra_names != set():
        list_extra_names = sorted(extra_names)
        print("\nHipparcos stars that are in", in_name.upper(), "but not in", out_name.upper())
        outer_count = 0
        count = 0
        names_string = ""
        for extra_name in list_extra_names:
            if extra_name not in star_to_ignore:
                outer_count += 1
                count += 1
                names_string += extra_name + " "
                if count == 5:
                    print(names_string)
                    count = 0
                    names_string = ""
        if count != 5:
            print(names_string)
        print("Total: (" + str(outer_count) + ")\n")
        for hip_name in list_extra_names:
            in_star_dict[hip_name]['hip'] = hip_name
        return [in_star_dict[hip_name] for hip_name in list_extra_names]
    else:
        return []


def overlap_parm_in_one_star(params_only, single_star_dict, overlap_dict_this_star, name):
    for param in params_only:
        if param != "blank":
            overlap_dict_this_star[name][param] = single_star_dict[param]
    return overlap_dict_this_star


def same_diff_dict(the_dict, param, value1, value2, name1, name2):
    try:
        if value1 == value2 or 0.011 > abs(value1 - value2) or (value1 == float("nan") and value2 == ""):
            the_dict['same'][param] = value1
        else:
            the_dict['diff'][param] = {name1: value1, name2: value2}
    except TypeError:
        if param == "2MASS":
            if value1 == "" and ("-" in value2 or "+" in value2):
                the_dict['same'][param] = value2
            else:
                the_dict['diff'][param] = {name1: value1, name2: value2}
        elif param == "hd":
            try:
                if value1 == float(value2[:-1]):
                    the_dict['same'][param] = value2
                else:
                    the_dict['diff'][param] = {name1: value1, name2: value2}
            except (TypeError, ValueError):
                the_dict['diff'][param] = {name1: value1, name2: value2}
        else:
            the_dict['diff'][param] = {name1: value1, name2: value2}
    return the_dict


def compare_outputs(output1, output2, params_to_exclude, star_to_ignore):
    name1, star_dict1 = output1
    name2, star_dict2 = output2
    hip_names1 = set(star_dict1.keys())
    hip_names2 = set(star_dict2.keys())
    extra_names1 = hip_names1 - hip_names2
    extra_names2 = hip_names2 - hip_names1
    common_names = hip_names1 & hip_names2

    # star names with no overlap in the two data sets
    extra2 = extra_stars(extra_names2, name2, name1, star_dict2, star_to_ignore)
    extra1 = extra_stars(extra_names1, name1, name2, star_dict1, star_to_ignore)

    # stars that are in both outputs
    overlap = []
    issues = []
    for overlap_name in sorted(common_names):
        overlap_dict_this_star = {"same": {}, "diff": {}, name1: {}, name2: {}}
        # The hip name is the same in both by definition of reaching this point in the code
        overlap_dict_this_star["same"]["hip"] = overlap_name
        # get the parameters of each star
        params_star1 = set(star_dict1[overlap_name].keys())
        params_star2 = set(star_dict2[overlap_name].keys())

        overlap_dict_this_star = overlap_parm_in_one_star(params_star1 - params_star2, star_dict1[overlap_name],
                                                          overlap_dict_this_star, name1)
        overlap_dict_this_star = overlap_parm_in_one_star(params_star2 - params_star1, star_dict2[overlap_name],
                                                          overlap_dict_this_star, name2)
        for param in (params_star1 & params_star2) - params_to_exclude:
            if type(star_dict1[overlap_name][param]) == dict:
                catalog_dict = {"same": {}, "diff": {}, name1: {}, name2: {}}
                catalog_params1 = set(star_dict1[overlap_name][param].keys())
                catalog_params2 = set(star_dict2[overlap_name][param].keys())
                catalog_dict = overlap_parm_in_one_star(catalog_params1 - catalog_params2,
                                                        star_dict1[overlap_name][param],
                                                        catalog_dict, name1)
                catalog_dict = overlap_parm_in_one_star(catalog_params2 - catalog_params1,
                                                        star_dict2[overlap_name][param],
                                                        catalog_dict, name2)
                for cat_par in (catalog_params1 & catalog_params2) - params_to_exclude:
                    catalog_dict = same_diff_dict(catalog_dict, cat_par,
                                                  star_dict1[overlap_name][param][cat_par],
                                                  star_dict2[overlap_name][param][cat_par], name1, name2)
                if any([catalog_dict["diff"] != {}, catalog_dict[name1] != {}, catalog_dict[name2] != {}]):
                    overlap_dict_this_star['diff'][param] = catalog_dict
                else:
                    overlap_dict_this_star['same'][param] = catalog_dict
            else:
                overlap_dict_this_star = same_diff_dict(overlap_dict_this_star, param, star_dict1[overlap_name][param],
                                                        star_dict2[overlap_name][param], name1, name2)
        overlap.append(overlap_dict_this_star)
        if any([overlap_dict_this_star["diff"] != {}, overlap_dict_this_star[name1] != {},
                overlap_dict_this_star[name2] != {}]):
            issues.append(overlap_dict_this_star)

    return extra1, extra2, overlap, issues


def compare_ref_files(file_name1, file_name2):
    with open(file_name1, 'r') as f:

        set1 = set(f.read().split("\n"))

    with open(file_name2, 'r') as f:
        set2 = set(f.read().split("\n"))

    in1 = list(set1 - set2)
    in1_dict = {}
    for line in in1:
        items_list = line.split(",")
        for item in items_list:
            if item[:len("Gaia DR@")] == "Gaia DR2":
                in1_dict[item] = items_list

    in2 = list(set2 - set1)
    in2_dict = {}
    for line in in2:
        items_list = line.split(",")
        for item in items_list:
            if item[:len("Gaia DR@")] == "Gaia DR2":
                in2_dict[item] = items_list

    return set1 & set2, in1_dict, in2_dict


if __name__ == "__main__":
    too_far_stars = {"100345", "102703", "107818",
                     "108090", "1269", "12720",
                     "13274", "21000", "22220",
                     "27111", "33628", "36474",
                     "40231", "46893", "47267",
                     "4804", "49166", "52942",
                     "5445", "54957", "5544",
                     "62608", "69753", "70038",
                     "71142", "76427", "7837",
                     "78850", "90659", "9367",
                     "96428", "97984", "9870",
                     "13989"}
    weird_spectral_type = {"45075", "58327"}
    updated_binary_names = {"103569"}
    star_to_ignore = too_far_stars | weird_spectral_type | updated_binary_names
    # emulate_legacy()
    old_output = load_from_text(legacy_file_name)
    new_output = load_from_text(new_file_name)

    extra1, extra2, overlap, issues = compare_outputs(("legacy", old_output), ("new", new_output),
                                                      params_to_exclude={"Position", 'dist (pc)','2MASS',
                                                                         "Dec proper motion", 'RA proper motion'},
                                                      star_to_ignore=star_to_ignore)

    # same, in1, in2 = compare_ref_files(os.path.join(working_dir, "load", "reference_data", "gaia_query_data5.2.csv"),
    #                                    os.path.join(working_dir, "load", "reference_data", "gaia_query_data_5.3.csv"))
