import os
import math

import numpy as np


from hypatia.elements import element_rank, ElementID
from hypatia.plots.scatter_hist_hist_plot import histPlot
from hypatia.pipeline.star.output import load_pickled_output
from hypatia.configs.source_settings import norm_keys_default
from hypatia.pipeline.nat_cat import NatCat, load_catalog_query
from hypatia.configs.file_paths import target_list_dir, base_dir, pickle_nat


def save_or_load(load=True, a_catalog_query=None):
    """
    A single function the saves the state of a Hypatia catalog query (often this is saved to the a variable named
    nat_cat) after it is loaded, or loads a previously saved catalog query.
    This is different from other intermediate data products as it save the complete state of the catalog query.
    This is a way to get back to exactly where you were when operating on a catalog query that was closed, or for
    comparing several instances of a catalog query. Of course the methods of CatalogQuery can be accesses directly,
    skipping this rather basic definition.

    :param load: bool - Toggles the load state when True and the save state when False
    :param a_catalog_query: an instance of CatalogQuery (usually in the variable named nat_cat) to save.
    :return: When load=True, this returns the requested instance of CatalogQuery.
    """
    if load:
        return load_catalog_query()
    else:
        a_catalog_query.pickle_myself()


def standard_output(from_scratch=True, refresh_exo_data=False, short_name_list=None, norm_keys: list[str] = None,
                    target_list: list[str] | list[tuple[str, ...]] | str | os.PathLike | None = None,
                    fast_update_gaia=True, from_pickled_cat: bool = False, from_pickled_output: bool = False,
                    mongo_upload: bool = True):
    target_output = None
    params = ["dist", "logg", 'Teff', "SpType", 'st_mass', 'st_rad', "disk"]
    star_name_type = ['gaia dr2', "gaia dr1", "hip", 'hd', "wds"]
    if short_name_list is None:
        catalogs_file_name = None
    else:
        catalogs_file_name = 'subset_catalog_file.csv'

    if from_pickled_cat and os.path.exists(pickle_nat):
        nat_cat = load_catalog_query()
    else:
        nat_cat = NatCat(params_list_for_stats=params,
                         star_types_for_stats=star_name_type,
                         catalogs_from_scratch=from_scratch, verbose=True, catalogs_verbose=True,
                         get_abundance_data=True, get_exo_data=True, refresh_exo_data=refresh_exo_data,
                         target_list=target_list,
                         fast_update_gaia=fast_update_gaia,
                         catalogs_file_name=catalogs_file_name)
        nat_cat.pickle_myself()
    if from_pickled_output:
        output_star_data = load_pickled_output()
    else:

        dist_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                                    parameter_bound_filter=[('dist', 0, 500), ("Teff", 2300.0, 7500.)],
                                                    star_data_stats=False,
                                                    reduce_abundances=False)

        exo_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                                   parameter_bound_filter=None,
                                                   has_exoplanet=True,
                                                   star_data_stats=False,
                                                   reduce_abundances=False)
        if target_list is None:
            output_star_data = dist_output + exo_output
        else:
            # select only the data that is belongs to the list of target stars
            target_output = nat_cat.make_output_star_data(is_target=True)
            output_star_data = target_output
        # optional 2nd filtering step
        output_star_data.filter(target_catalogs=None, or_logic_for_catalogs=True,
                                catalogs_return_only_targets=False,
                                target_star_name_types=None, and_logic_for_star_names=True,
                                target_params=None, and_logic_for_params=True,
                                target_elements=None, or_logic_for_element=True,
                                element_bound_filter=None,  # filtering happens before normalization
                                min_catalog_count=None,
                                parameter_bound_filter=None,
                                parameter_match_filter=None,
                                at_least_fe_and_another=True,
                                remove_nlte_abundances=False,
                                keep_complement=False,
                                is_target=None)
        output_star_data.normalize(norm_keys=norm_keys)
        output_star_data.filter(element_bound_filter=None)  # filter after normalization, and logic
        output_star_data.do_stats(params_set=nat_cat.params_list_for_stats,
                                  star_name_types=nat_cat.star_types_for_stats)
        if mongo_upload:
            output_star_data.reduce_elements()
            output_star_data.find_available_attributes()
            output_star_data.export_to_mongo(catalogs_file_name=nat_cat.catalogs_file_name)
        output_star_data.pickle_myself()
    return nat_cat, output_star_data, target_output


def multi_output(from_scratch=True, short_name_list=None, norm_key=None, fast_update_gaia=False):
    params = ["dist", "logg", 'Teff', "SpType", 'st_mass', 'st_rad', "disk"]
    star_name_type = ['gaia- dr2', "gaia dr1", "hip", 'hd', "wds"]
    if short_name_list is None:
        catalogs_file_name = None
    else:
        catalogs_file_name = 'subset_catalog_file.csv'

    nat_cat = NatCat(params_list_for_stats=params,
                     star_types_for_stats=star_name_type,
                     catalogs_from_scratch=from_scratch, verbose=True, catalogs_verbose=True,
                     get_abundance_data=True, get_exo_data=True, refresh_exo_data=from_scratch,
                     fast_update_gaia=fast_update_gaia,
                     catalogs_file_name=catalogs_file_name)
    nat_cat.pickle_myself()

    dist_output1 = nat_cat.make_output_star_data(min_catalog_count=1,
                                                 parameter_bound_filter=[("Teff", 2300.0, 7500.)],
                                                 star_data_stats=False,
                                                 reduce_abundances=False)

    exo_output1 = nat_cat.make_output_star_data(min_catalog_count=1,
                                                parameter_bound_filter=None,
                                                has_exoplanet=True,
                                                star_data_stats=False,
                                                reduce_abundances=False)
    output_star_data1 = dist_output1 + exo_output1
    output_star_data1.filter(target_catalogs=None, or_logic_for_catalogs=True,
                             catalogs_return_only_targets=False,
                             target_star_name_types=None, and_logic_for_star_names=True,
                             target_params=None, and_logic_for_params=True,
                             target_elements=None, or_logic_for_element=True,
                             element_bound_filter=None,  # filtering happens before normalization
                             min_catalog_count=None,
                             parameter_bound_filter=None,
                             parameter_match_filter=None,
                             at_least_fe_and_another=True,
                             remove_nlte_abundances=True,
                             keep_complement=False)
    if norm_key is not None:
        output_star_data1.normalize(norm_key=norm_key)
    output_star_data1.filter(element_bound_filter=None)  # filter after normalization, and logic
    output_star_data1.do_stats(params_set=nat_cat.params_list_for_stats,
                               star_name_types=nat_cat.star_types_for_stats)
    output_star_data1.reduce_elements()
    output_star_data1.find_available_attributes()

    dist_output2 = nat_cat.make_output_star_data(min_catalog_count=1,
                                                 parameter_bound_filter=[('dist', 0, 100), ("Teff", 5680.0, 5880.)],
                                                 # 2300.0, 7500.0
                                                 star_data_stats=False,
                                                 reduce_abundances=False)

    exo_output2 = nat_cat.make_output_star_data(min_catalog_count=1,
                                                parameter_bound_filter=[('dist', 0, 100), ("Teff", 5680.0, 5880.)],
                                                has_exoplanet=True,
                                                star_data_stats=False,
                                                reduce_abundances=False)
    output_star_data2 = dist_output2 + exo_output2
    output_star_data2.filter(target_catalogs=None, or_logic_for_catalogs=True,
                             catalogs_return_only_targets=False,
                             target_star_name_types=None, and_logic_for_star_names=True,
                             target_params=None, and_logic_for_params=True,
                             target_elements=None, or_logic_for_element=True,
                             element_bound_filter=None,  # filtering happens before normalization
                             min_catalog_count=None,
                             parameter_bound_filter=[('logg', 4.34, 4.54)],
                             parameter_match_filter=None,
                             at_least_fe_and_another=True,
                             remove_nlte_abundances=True,
                             keep_complement=False)
    if norm_key is not None:
        output_star_data2.normalize(norm_key=norm_key)
    output_star_data2.filter(element_bound_filter=[("Fe", -0.1, 0.1)])  # filter after normalization, and logic
    output_star_data2.do_stats(params_set=nat_cat.params_list_for_stats,
                               star_name_types=nat_cat.star_types_for_stats)
    output_star_data2.reduce_elements()
    output_star_data2.find_available_attributes()
    return nat_cat, output_star_data1, output_star_data2


def element_plot(output_star_data, divide_by: str = "Fe", numerators: list[str] = None):
    if numerators is None:
        numerators = ["Si", "Fe", "Mg"]
    element_list = numerators[:]
    numerators.remove(divide_by)
    star_names_list = list(sorted(output_star_data.star_names))
    dict_to_element_array = {}
    for element in element_list:
        dict_to_element_array[element] = np.array([output_star_data.__getattribute__(star_name)
                                                  .reduced.__getattribute(element).median
                                                   for star_name in star_names_list])
    division_arrays = [dict_to_element_array[numerator] - dict_to_element_array[divide_by]
                       for numerator in numerators]
    histPlot(xdata=division_arrays[0], ydata=division_arrays[1],
             xxlabel="[" + numerators[0] + "/" + divide_by + "]", yylabel="[" + numerators[1] + "/" + divide_by + "]",
             saveFigure=True)


def make_element_distance_plots(from_scratch=True):
    nat_cat = NatCat(catalogs_from_scratch=from_scratch, verbose=True,
                     get_abundance_data=True, get_exo_data=True, refresh_exo_data=False)
    nat_cat.star_data.get_element_ratio_and_distance(element_set=None,
                                                     distance_list=[0.0, 30.0, 60.0, 90.0, 150.0, 500.0],
                                                     xlimits_list=None, ylimits_list=None, has_exoplanet=None,
                                                     use_median=True)
    return nat_cat


def output_ref_abundances(catalogs_file_name=None):
    if catalogs_file_name is None:
        catalogs_file_name = 'catalog_file.csv'

    nat_cat = NatCat(catalogs_from_scratch=True, verbose=True, catalogs_verbose=True,
                     get_abundance_data=True, get_exo_data=False, refresh_exo_data=False,
                     catalogs_file_name=catalogs_file_name)
    nat_cat.output_abs_abundances()
    nat_cat.output_raw_abundances()


def print_single_star_abunds(star_name):
    check = output_star_data.get_single_star_data(star_name)
    elems = list(sorted(check.reduced_abundances.available_abundances, key=element_rank))
    for elem in elems:
        print(elem, check.reduced_abundances.__getattribute__(elem).median,
              check.reduced_abundances.__getattribute__(elem).spread,
              check.reduced_abundances.__getattribute__(elem).len)
        print('\n')
    print(check.reduced_abundances.Fe.catalog_list)
    print(check.reduced_abundances.Fe.value_list)


def plot_all(xaxis):
    """
    :param xaxis: The elements will be plotted on the y-axis, this allows you to specify the x-axis
    :return: plots saved to /xy_plot
    """
    elems = list(sorted(stats.star_count_per_element.available_bins, key=element_rank))
    for elem in elems:
        output_star_data.xy_plot(x_thing=xaxis, y_thing=elem, color="darkorchid", show=False, save=True)


def find_outliers(workingelem, ltgt, bound):
    '''
    Example: find_outliers('P', 'gt',-1.0)
    :param workingelem: The elements you are interested in as a string
    :param ltgt: Either 'lt' or 'gt'
    :param bound: The boundary above or below which you are interested (float)
    :return: Printed to screen
    '''
    star_names_list = list(sorted(output_star_data.star_names))
    elemdict = {}
    for star_name in star_names_list:
        single_star = output_star_data.__getattribute__(star_name)
        available_catalogs = single_star.available_abundance_catalogs
        if 'Teff' in single_star.params.available_params:
            temp = single_star.params.__getattribute__('Teff')
        else:
            temp = None
        for catalog_name in available_catalogs:
            single_catalog = single_star.__getattribute__(catalog_name)
            available_abundances = single_catalog.available_abundances
            if workingelem in available_abundances:
                value = single_catalog.__getattribute__(workingelem)
                origname = single_catalog.original_catalog_star_name.type + \
                           str(single_catalog.original_catalog_star_name.id)
                elemdict.update({star_name: (value, origname, temp, catalog_name)})
    for star, value in elemdict.items():
        if ltgt == 'lt':
            if value[0] < bound:
                print(star, value)
        elif ltgt == 'gt':
            if value[0] > bound:
                print(star, value)
        else:
            print('Improper bounds -- please enter lt or gt.')


def calc_molar_fractions(elemlist, solarvals, errvals, **kwargs):
    """

       histPlot(molarX, molarY, exoXdata=exo_molarX, exoYdata=exo_molarY, linecolor='purple',
             addedScatterX=1., addedScatterY=50.,
             xxlabel=Xnum+"/"+Xdenom, yylabel=Ynum+"/"+Ydenom,
             xbinLeft=0, xbinRight=32.0,
             ybinLeft=0., ybinRight=2500.,
             x_bin_number=20, y_bin_number=20, redfield_ratios=True,
             saveFigure=True, figname="scatter_hist_hist/"+Xnum+Xdenom+"vs"+Ynum+Ydenom)

    Could run this on the output created from picklemyself, without having to reload or copy and paste
    """
    Xnum, Xdenom, Ynum, Ydenom = elemlist
    Xnum_sol, Xdenom_sol, Ynum_sol, Ydenom_sol = solarvals
    Xnum_err, Xdenom_err, Ynum_err, Ydenom_err = errvals
    star_names_list = list(sorted(output_star_data.star_names))
    med_elem_dict = {single_element: [] for single_element in set(elemlist)}
    exo_med_elem_dict = {single_element: [] for single_element in set(elemlist)}
    for star_name in star_names_list:
        single_star = output_star_data.__getattribute__(star_name)
        if set(elemlist).issubset(single_star.reduced_abundances.available_abundances):
            for workingelem in set(elemlist):
                if "exo" in single_star.available_data_types:
                    exo_median = single_star.reduced_abundances.__getattribute__(workingelem).median
                    exo_med_elem_dict[workingelem].append(exo_median)
                else:
                    median = single_star.reduced_abundances.__getattribute__(workingelem).median
                    med_elem_dict[workingelem].append(median)

    molarX = [10 ** (med_elem_dict[Xnum][kk] + Xnum_sol - (med_elem_dict[Xdenom][kk] + Xdenom_sol)) for kk in
              range(len(med_elem_dict[Xnum]))]
    molarY = [10 ** (med_elem_dict[Ynum][kk] + Ynum_sol - (med_elem_dict[Ydenom][kk] + Ydenom_sol)) for kk in
              range(len(med_elem_dict[Ynum]))]

    XnumXdenomerr = (10 ** (math.sqrt(Xnum_err ** 2 + Xdenom_err ** 2)) - 1.) * np.median(molarX)
    YnumYdenomerr = (10 ** (math.sqrt(Ynum_err ** 2 + Ydenom_err ** 2)) - 1.) * np.median(molarY)

    exo_molarX = [10 ** (exo_med_elem_dict[Xnum][kk] + Xnum_sol - (exo_med_elem_dict[Xdenom][kk] + Xdenom_sol)) for kk
                  in
                  range(len(exo_med_elem_dict[Xnum]))]
    exo_molarY = [10 ** (exo_med_elem_dict[Ynum][kk] + Ynum_sol - (exo_med_elem_dict[Ydenom][kk] + Ydenom_sol)) for kk
                  in range(len(exo_med_elem_dict[Ynum]))]

    print("Total number of stars is", len(molarX) + len(exo_molarX), "where", len(exo_molarX),
          "are exoplanet host stars")

    histPlot(molarX, molarY, exoXdata=exo_molarX, exoYdata=exo_molarY, xerror=XnumXdenomerr, yerror=YnumYdenomerr,
             linecolor=kwargs["linecolor"],
             addedScatterX=kwargs["addedScatterX"], addedScatterY=kwargs["addedScatterY"],
             xbinLeft=kwargs["xbinLeft"], xbinRight=kwargs["xbinRight"],
             ybinLeft=kwargs["ybinLeft"], ybinRight=kwargs["ybinRight"],
             x_bin_number=kwargs["x_bin_number"], y_bin_number=kwargs["y_bin_number"],
             redfield_ratios=kwargs["redfield_ratios"], saveFigure=kwargs["saveFigure"], do_pdf=kwargs["do_pdf"],
             xxlabel=Xnum + "/" + Xdenom, yylabel=Ynum + "/" + Ydenom,
             figname="scatter_hist_hist/" + Xnum + Xdenom + "vs" + Ynum + Ydenom)


elem_list_default = ["Fe","Mg", "Si", "Al", "Ti", "Ti_II", "Y", "Y_II", "Ba_II", "Cs"]
property_list_default = ["teff", "logg"]#None if no list

def create_flat_file(filename, targetList, elemList=None, propertyList=None):
    """
    Examples of the input (these are used by Amilcar for planetPrediction):
    elemList=["Fe","Li","C","O","Na","Mg","Al","Si","Ca","Sc","Ti","V","Cr","Mn","Co","Ni","Y"]
    propertyList=["raj2000", "decj2000", "x_pos", "y_pos", "z_pos", "dist", "disk", "sptype", "vmag",
                             "bv", "u_vel", "v_vel", "w_vel", "teff", "logg", "mass", "rad"]
    filename="hypatia/HyData/target_lists/hypatiaUpdated_flat_file.csv"
    targetList = ClassyReader(filename="hypatia/HyData/target_lists/HWO-FP-Tier1-2-stars.csv")

    Note that the elements shouldn't have an "H" appended at the end. Also, header names will differ from the
    website output for the properties since the "f_" prefix was done by Dan.

    To output the results from the Mdwarf subsets in sandbox, change output_star_data to target_star_data
    and switch lodders09 to absolute.

    create_flat_file(elemList, propertyList, filename, targetList)
    """

    with open(os.path.join(base_dir, filename), "w") as combined_data_file:
        if targetList is not None:
            header = "HPIC_name,star_name," + ",".join(elemList) + "," + ",".join(propertyList) + "\n"
            combined_data_file.write(header)
            for star in targetList.Star:
                originalName = star
                temp = output_star_data.get_single_star_data(star)
                if temp is None:
                    combined_data_file.write(f'{originalName}'+ "\n")
                else:
                    combined_data_file.write(f'{originalName},')
                    star_name = temp.attr_name
                    populate_flat_file(elemList, propertyList, star_name, combined_data_file)
        else:
            if propertyList is not None:
                header = "star_name," + ",".join(elemList) + "," + ",".join(propertyList) + "\n"
            else:
                header = "star_name," + ",".join(elemList) + "," + "\n"
            combined_data_file.write(header)
            star_names_list = list(sorted(output_star_data.star_names))
            for star in star_names_list:  #what is a better way to get the attr name?
                star_name = output_star_data.get_single_star_data(star).attr_name
                populate_flat_file(elemList, propertyList, star_name, combined_data_file)

def populate_flat_file(elemList, propertyList, star_name, combined_data_file):
    single_star = output_star_data.__getattribute__(star_name)
    combined_data_file.write(f'{single_star.star_reference_name},')
    values = []
    for element in elemList:
        elemID = ElementID.from_str(element)
        elemsAvailable = single_star.reduced_abundances['lodders09'].available_abundances
        if elemID in elemsAvailable:
            values.append(str(round(single_star.reduced_abundances['lodders09'].__getattribute__(element).median, 2)))
        else:
            values.append('nan')
    combined_data_file.write(",".join(values))
    properties = []
    if propertyList is not None:
        for property in propertyList:
            if property in single_star.params.available_params:
                # Note that some stars have x, y, z pos parameters, others have pos (embedded),
                # and others have both. The below will miss the ones with only pos (embedded).
                if property == "x_pos":
                    properties.append(str(round(single_star.params.pos[0][0], 3)))
                elif property == "y_pos":
                    properties.append(str(round(single_star.params.pos[0][1], 3)))
                elif property == "z_pos":
                    properties.append(str(round(single_star.params.pos[0][2], 3)))
                elif property == "teff_ref":
                    properties.append(single_star.params.teff.ref)
                elif property == "logg_ref":
                    properties.append(single_star.params.logg.ref)
                else:
                    properties.append(str(single_star.params.__getattribute__(property).value))
                    properties.append(str(single_star.params.__getattribute__(property).ref))
            else:
                properties.append('nan')
    all_params.update(single_star.params.available_params)
    combined_data_file.write("," + ",".join(properties) + "\n")


if __name__ == "__main__":
    only_target_list = False

    all_params = set()
    test_norm_keys = list(norm_keys_default)
    test_refresh_exo_data = True
    test_from_scratch = True
    test_from_pickled_cat = False
    mongo_upload=False
    if only_target_list:
        example_target_list = os.path.join(target_list_dir, 'Patrick-XRP-target-list-cut.csv')
        # example_target_list2 = ['HIP 36366', 'HIP 55846', 'HD 103095', 'HIP 33226']
        nat_cat, output_star_data, target_star_data = standard_output(from_scratch=test_from_scratch,
                                                                      target_list=example_target_list,
                                                                      norm_keys=test_norm_keys,
                                                                      refresh_exo_data=test_refresh_exo_data,
                                                                      from_pickled_cat=test_from_pickled_cat,
                                                                      mongo_upload=mongo_upload
                                                                      )
    else:
        nat_cat, output_star_data, target_star_data = standard_output(from_scratch=test_from_scratch,
                                                                      norm_keys=test_norm_keys,
                                                                      refresh_exo_data=test_refresh_exo_data,
                                                                      from_pickled_cat=test_from_pickled_cat,
                                                                      mongo_upload=mongo_upload
                                                                      )

    # output_star_data.xy_plot(x_thing='dist', y_thing='Fe', color="darkorchid", show=False, save=True)
    stats = output_star_data.stats
    # output_star_data.flat_database_output()
    stars_all = nat_cat.star_data.star_names
    print(len(stars_all), "total stars")
    stars_hypatia = output_star_data.star_names
    print(len(stars_hypatia), "stars after cuts")
    print(stats.stars_with_exoplanets, "stars with exoplanets")
