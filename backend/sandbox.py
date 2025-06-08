"""
Nat's Test Space

The current code below takes the input file (no spaces between commas, often a "planets_" file from NEA)
and creates a mini-sources by matching only to those stars while still retaining all of the tools and
stats of the main Hypatia sources. To execute, run this file in the terminal. Might need to move this to
standard_lib at some point.
"""
import os

from hypatia.pipeline.nat_cat import NatCat
from hypatia.configs.file_paths import hydata_dir
from sakhmet_tools import mdwarf_histogram
from hypatia.configs.source_settings import norm_keys_default


def mdwarf_output(target_list: list[str] | list[tuple[str, ...]] | str | os.PathLike | None = None,
                 catalogs_file_name: str = os.path.join(hydata_dir, 'subsets', 'mdwarf_subset_catalog_file.csv'), # 'reference_data', 'catalog_file.csv'
                 refresh_exo_data=False, norm_keys: list[str] = None,
                 params_list_for_stats: list[str] = None, star_types_for_stats: list[str] = None,
                 parameter_bound_filter: list[tuple[str, int | float | str, int| float | str]] = None,
                 mongo_upload: bool = True):
    if params_list_for_stats is None:
        params_list_for_stats = ["dist", "logg", 'Teff', "SpType", 'st_mass', 'st_rad', "disk"]
    if star_types_for_stats is None:
        star_types_for_stats = ['gaia dr2', "gaia dr1", "hip", 'hd', "wds"]
    if parameter_bound_filter is None:
        parameter_bound_filter = [("Teff", 2300.0, 4000.), ("logg", 3.5, 6.0), ("dist", 0.0, 30.0)]
    nat_cat = NatCat(params_list_for_stats=params_list_for_stats,
                     star_types_for_stats=star_types_for_stats,
                     catalogs_from_scratch=True, verbose=True, catalogs_verbose=True,
                     get_abundance_data=True, get_exo_data=True, refresh_exo_data=refresh_exo_data,
                     target_list=target_list,
                     catalogs_file_name=catalogs_file_name)
    dist_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                                parameter_bound_filter=parameter_bound_filter,
                                                star_data_stats=False,
                                                reduce_abundances=False)

    exo_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                               parameter_bound_filter=None,
                                               has_exoplanet=True,
                                               star_data_stats=False,
                                               reduce_abundances=False)
    # sort by is the data a target star
    target_output = nat_cat.make_output_star_data(is_target=True)
    output_star_data = dist_output + exo_output + target_output
    # optional 2nd filtering step
    # Check mission elements: {'C','N','O','F','Na','Mg','Si','Cl','K','Ca','Ti'} -- True
    # Both Mg and Si measurements: {'Mg','Si'} -- False
    # Also look at target overlap
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
                            remove_nlte_abundances=True,
                            keep_complement=False,
                            is_target=None)
    output_star_data.normalize(norm_keys=norm_keys)
    output_star_data.filter(element_bound_filter=None)  # filter after normalization, and logic
    output_star_data.do_stats(params_set=nat_cat.params_list_for_stats,
                              star_name_types=nat_cat.star_types_for_stats)
    output_star_data.reduce_elements()
    output_star_data.find_available_attributes()
    if mongo_upload:
        output_star_data.export_to_mongo(catalogs_file_name=nat_cat.catalogs_file_name)
    output_star_data.pickle_myself()
    return nat_cat, output_star_data, target_output


# the nonMs are being manually added back in, not removed
# these need to be removed: 'LP 714-47', 'HD 97101', 'HD 168442'
# nonMs = ['HD 88230', 'HD 178126', 'LHS 104', 'LHS 170', 'LHS 173', 'LHS 236', 'LHS 343', 'LHS 467', 'LHS 1138', 'LHS 1482','LHS 1819','LHS 1841', 'LHS 2161', 'LHS 2463', 'LHS 2715', 'LHS 2938', 'LHS 3084', 'HIP 27928', 'G 39-36', 'HIP 37798', 'HIP 67308', 'LHS 1229', 'HD 11964B', 'HD 18143B', 'HD 285804', 'BD-01 293B', 'BD+17 719C', 'BD+24 0004B', 'GJ 129', 'GJ 1177B', '2MASS 2203769-2452313', 'HD 35155', 'HD 49368', 'HD 120933', 'HD 138481', 'HD 10380', 'HD 10824', 'HD 15656', 'HD 20468', 'HD 20644', 'HD 23413', 'HD 29065', 'HD 52960', 'HD 58972', 'HD 62721', 'HD 88230', 'HD 218792', 'HD 223719', 'HD 225212', 'HD 6860', 'HD 18191', 'HD 18884', 'HD 30959', 'HD 35155', 'HD 44478', 'HD 49368', 'HD 71250', 'HD 112300', 'HD 119228', 'HD 120933', 'HD 138481', 'HD 147923', 'HD 216386', 'HD 224935', 'HD 10380', 'HD 10824', 'HD 15656', 'HD 20468', 'HD 20644', 'HD 23413', 'HD 29065', 'HD 52960', 'HD 58972', 'HD 60522', 'HD 62721', 'HD 88230', 'HD 218792', 'HD 223719', 'HD 225212']
all_params = set()

test_norm_keys = list(norm_keys_default)
test_refresh_exo_data = False
test_from_scratch = True
test_from_pickled_cat = False
target_list_file = "hypatia/HyData/target_lists/hypatia_mdwarf_cut_justnames.csv"
#target_list = os.path.join(ref_dir, 'hypatia_mdwarf_cut_justnames.csv')

nat_cat, output_star_data, target_star_data = mdwarf_output(norm_keys=test_norm_keys,
                                                            target_list=target_list_file,
                                                            refresh_exo_data=test_refresh_exo_data)
stats = target_star_data.stats

mdwarf_histogram(stats.star_count_per_element)
# Note to self: To run this, run directly in a Python terminal
