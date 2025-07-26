import os

from sandbox import mdwarf_histogram, multi_scatter_plot
from hypatia.elements import element_rank, ElementID
from hypatia.pipeline.star.output import load_pickled_output
from hypatia.configs.source_settings import norm_keys_default
from hypatia.pipeline.nat_cat import NatCat, load_catalog_query
from hypatia.configs.file_paths import target_list_dir, base_dir, pickle_nat, default_catalog_file, hydata_dir


def output_ref_abundances(catalogs_file_name=None):
    '''
    Creates folders under abundance_data where all abundances files are reprocessed in absolute or raw abundances.
    '''
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


def find_outliers(workingelem, ltgt, bound):
    '''
    Example: find_outliers('P', 'gt',-1.0)
    :param workingelem: The elements you are interested in as a string
    :param ltgt: Either 'lt' or 'gt'
    :param bound: The boundary above or below which you are interested (float)
    :return: Printed to screen
    '''
    elemdict = {}
    for single_star in output_star_data:
        available_catalogs = single_star.available_abundance_catalogs
        if 'Teff' in single_star.params.available_params:
            temp = single_star.params.__getattribute__('Teff')
        else:
            temp = None
        for catalog_name in available_catalogs:
            single_catalog = single_star.__getattribute__(catalog_name)
            elemID = ElementID.from_str(workingelem)
            elemsAvailable = single_star.reduced_abundances['lodders09'].available_abundances
            if elemID in elemsAvailable:
                value = float(single_catalog.__getattribute__('lodders09').__getattribute__(workingelem))
                origname = str(single_catalog.original_catalog_star_name)
                elemdict.update({single_star.star_reference_name: (value, origname, temp, catalog_name)})
    for star, value in elemdict.items():
        if ltgt == 'lt':
            if value[0] < bound:
                print(star, value)
        elif ltgt == 'gt':
            if value[0] > bound:
                print(star, value)
        else:
            print('Improper bounds -- please enter lt or gt.')


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

def standard_output(from_scratch=True, refresh_exo_data=False, norm_keys: list[str] = None,
                    fast_update_gaia=True, from_pickled_cat: bool = False, from_pickled_output: bool = False,
                    mongo_upload: bool = True,
                    catalogs_file_name: str = default_catalog_file,
                    target_list: list[str] | list[tuple[str, ...]] | str | os.PathLike | None = None,
                    params_list_for_stats: list[str] = None, star_types_for_stats: list[str] = None,
                    dist: tuple[float | None, float | None] | None = (0.0, 500.0),
                    teff: tuple[float | None, float | None] | None = (2300.0, 7500.0),
                    logg: tuple[float | None, float | None] | None = None,
                    ):
    target_output = None
    if params_list_for_stats is None:
        params_list_for_stats = ["dist", "logg", 'Teff', "SpType", 'st_mass', 'st_rad', "disk"]
    if star_types_for_stats is None:
        star_types_for_stats = ['gaia dr2', "gaia dr1", "hip", 'hd', "wds"]

    if from_pickled_cat and os.path.exists(pickle_nat):
        nat_cat = load_catalog_query()
    else:
        nat_cat = NatCat(params_list_for_stats=params_list_for_stats,
                         star_types_for_stats=star_types_for_stats,
                         catalogs_from_scratch=from_scratch, verbose=True, catalogs_verbose=True,
                         get_abundance_data=True, get_exo_data=True, refresh_exo_data=refresh_exo_data,
                         target_list=target_list,
                         fast_update_gaia=fast_update_gaia,
                         catalogs_file_name=catalogs_file_name)
        nat_cat.pickle_myself()
    if from_pickled_output:
        output_star_data = load_pickled_output()
    else:
        parameter_bound_filter = []
        if dist is not None:
            parameter_bound_filter.append(('dist', dist[0], dist[1]))
        if teff is not None:
            parameter_bound_filter.append(('teff', teff[0], teff[1]))
        if logg is not None:
            parameter_bound_filter.append(('logg', logg[0], logg[1]))

        dist_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                                    parameter_bound_filter=parameter_bound_filter,
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
        output_star_data.reduce_elements()
        output_star_data.find_available_attributes()
        if mongo_upload:
            output_star_data.export_to_mongo(catalogs_file_name=nat_cat.catalogs_file_name,
                                             target_web_data=nat_cat.target_web_data)
        output_star_data.pickle_myself()

    return nat_cat, output_star_data, target_output

if __name__ == "__main__":
    '''
    FFF = run normal
    TFF = run only target list
    FTF = run multi, both normal (unless changed)
    FTT = run multi, first normal, second targetlist
    TTT = run multi, first targetlist, second targetlist
    '''

    only_target_list = False

    run_multi_output = True
    multi_target_list = True

    run_mdwarf_hist = False

    all_params = set()
    run_norm_keys = list(norm_keys_default)
    run_refresh_exo_data = False
    run_from_scratch = True
    run_from_pickled_cat = False

    mongo_upload=False

    kwargs_output = dict(from_scratch=run_from_scratch,
                         norm_keys=run_norm_keys,
                         refresh_exo_data=run_refresh_exo_data,
                         from_pickled_cat=run_from_pickled_cat,
                         mongo_upload=mongo_upload,
                         )

    if only_target_list:
        #run_target_list = os.path.join(target_list_dir, 'Patrick-XRP-target-list-cut.csv')
        # run_target_list2 = ['HIP 36366', 'HIP 55846', 'HD 103095', 'HIP 33226']
        target_list_file = str(os.path.join(target_list_dir, 'hypatia_mdwarf_cut_justnames.csv'))
        catalog_file = str(os.path.join(hydata_dir, 'subsets', 'mdwarf_subset_catalog_file.csv'))
        kwargs_params = dict(teff=(2300.0, 4000.0), logg=(3.5, 6.0), dist=(0.0, 30.0),)
    else:
        target_list_file = None
        catalog_file = default_catalog_file
        kwargs_params = dict()

    nat_cat, output_star_data, target_star_data = standard_output(**kwargs_output,
                                                                  target_list=target_list_file,
                                                                  catalogs_file_name = catalog_file,
                                                                  **kwargs_params
                                                                  )

    if run_multi_output:
        if multi_target_list:
            target_list_file2 = str(os.path.join(target_list_dir, 'hypatia_mdwarf_cut_justnames.csv'))
            catalog_file2 = str(os.path.join(hydata_dir, 'subsets', 'mdwarf_subset_catalog_file.csv'))
            kwargs_params2 = dict(teff=(2300.0, 4000.0), logg=(3.5, 6.0), dist=(0.0, 30.0),)
        else:
            target_list_file2 = None
            catalog_file2 = default_catalog_file
            kwargs_params2 = dict()

        nat_cat2, output_star_data2, target_star_data2 = standard_output(**kwargs_output,
                                                                         target_list=target_list_file2,
                                                                         catalogs_file_name=catalog_file2,
                                                                         **kwargs_params2
                                                                         )

    # output_star_data.xy_plot(x_thing='dist', y_thing='Fe', color="darkorchid", show=False, save=True)
    stats = output_star_data.stats
    # output_star_data.flat_database_output()
    stars_all = nat_cat.star_data.star_names
    print(len(stars_all), "total stars")
    stars_hypatia = output_star_data.star_names
    print(len(stars_hypatia), "stars after cuts")
    print(stats.stars_with_exoplanets, "stars with exoplanets")

    if run_mdwarf_hist: mdwarf_histogram(stats.star_count_per_element)

    if run_multi_output:
        stats2 = output_star_data2.stats
        stars_all = nat_cat2.star_data.star_names
        print(len(stars_all), "total stars (second set)")
        stars_hypatia2 = output_star_data2.star_names
        print(len(stars_hypatia2), "stars (second set) after cuts")
        print(stats2.stars_with_exoplanets, "stars (second set) with exoplanets")

