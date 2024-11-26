import copy
import pickle

from hypatia.object_params import SingleParam
from hypatia.pipeline.star.db import HypatiaDB
from hypatia.pipeline.star.all import AllStarData
from hypatia.pipeline.summary import upload_summary
from hypatia.sources.simbad.ops import get_star_data
from hypatia.pipeline.params.filters import core_filter
from hypatia.legacy.data_formats import spectral_type_to_float
from hypatia.plots.element_rad_plot import make_element_distance_plots
from hypatia.config import pickle_out, default_catalog_file, MONGO_DATABASE


def load_pickled_output():
    return pickle.load(open(pickle_out, 'rb'))


class OutputStarData(AllStarData):
    distance_bin_default = [0.0, 30.0, 60.0, 150.0]

    def receive_data(self, star_data):
        self.__dict__.update(copy.deepcopy(star_data.__dict__))

    def pickle_myself(self):
        if self.verbose:
            print("Picking an entire Output Star Data class.\nFile name:", pickle_out)
        pickle.dump(self, open(pickle_out, 'wb'))
        if self.verbose:
            print("  pickling complete.")

    def receive_from_single_star_data(self, main_star_ids: list[str], single_star_dicts, star_data=None):
        if star_data is not None:
            self.receive_data(star_data)
        for single_star in self:
            self.__delattr__(single_star.attr_name)
        self.star_names = main_star_ids
        for main_id in self.star_names:
            single_star_data = single_star_dicts[main_id]
            self.__setattr__(single_star_data.attr_name, copy.deepcopy(single_star_data))

    def __add__(self, other):
        # get the data from this instance of OutputStarData
        new_output = OutputStarData()
        # a copy of this instance
        new_output.receive_data(star_data=self)
        # add in all the SingleStarData that is in other but not in the instance
        for star_name in other.star_names - self.star_names:
            simbad_doc = get_star_data(star_name, test_origin="OutputStarData")
            attr_name = simbad_doc['attr_name']
            main_id = simbad_doc['_id']
            new_output.__setattr__(attr_name, copy.deepcopy(other.__getattribute__(attr_name)))
            new_output.star_names.add(main_id)
        # For the star names that overlap, add all the available data types that are missing.
        for star_name in other.star_names & self.star_names:
            simbad_doc = get_star_data(star_name, test_origin="OutputStarData")
            attr_name = simbad_doc['attr_name']
            other_star_data = other.__getattribute__(attr_name)
            self_star_data = self.__getattribute__(attr_name)
            # add missing data_types
            for data_type in other_star_data.available_data_types - self_star_data.available_data_types:
                new_output.__getattribute__(attr_name)\
                    .__setattr__(data_type, copy.deepcopy(other_star_data.__getattribute__(data_type)))
                new_output.__getattribute__(attr_name).available_data_types.add(data_type)
                if data_type not in self.non_abundance_data_types:
                    new_output.__getattribute__(attr_name).available_abundance_catalogs.add(data_type)
        return new_output

    def filter_by_available_data_type(self, and_logic_for_multiples, target_types, return_only_targets=False,
                                      keep_compliment=False):
        data_types_removed = 0
        stars_removed = 0
        target_types = set(target_types)
        if self.verbose:
            if and_logic_for_multiples:
                logic_str = "using 'And' logic."
            else:
                logic_str = "using 'Or' logic."
            print("Filtering in for", target_types, logic_str)
        for single_star in self:
            available_data_types = single_star.available_data_types
            target_found_flag = core_filter(and_logic_for_multiples, target_types, available_data_types)
            if not (target_found_flag and not keep_compliment):
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
            elif return_only_targets:
                if keep_compliment:
                    for type_to_remove in target_types:
                        data_types_removed += 1
                        single_star.__delattr__(type_to_remove)
                        single_star.available_data_types.remove(type_to_remove)
                        try:
                            single_star.available_abundance_catalogs.remove(type_to_remove)
                        except KeyError:
                            pass
                else:
                    for type_to_remove in available_data_types - target_types:
                        data_types_removed += 1
                        single_star.__delattr__(type_to_remove)
                        single_star.available_data_types.remove(type_to_remove)
                        try:
                            single_star.available_abundance_catalogs.remove(type_to_remove)
                        except KeyError:
                            pass
        if self.verbose:
            print("  Stars Removed:", stars_removed, " Data Types removed:", data_types_removed)
            if self.star_names == set():
                print("    'filter_by_available_data_type' has ended with and empty set of data.")

    def filter_by_min_cat_count(self, minimum_cat_count, keep_compliment=False):
        stars_removed = 0
        if self.verbose:
            print("Filtering for Hypatia stars with at least", minimum_cat_count, "catalogs.")
        for single_star in self:
            available_data_types = single_star.available_abundance_catalogs
            if not (len(available_data_types) >= minimum_cat_count and not keep_compliment):
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed)
            if self.star_names == set():
                print("    'filter_by_min_cat_count' has ended with and empty set of data.")

    def filter_by_object_parameters(self, and_logic_for_multiples, target_types, keep_compliment=False):
        stars_removed = 0
        target_types = {target.lower() for target in target_types}
        if self.verbose:
            if and_logic_for_multiples:
                logic_str = "using 'And' logic."
            else:
                logic_str = "using 'Or' logic."
            print("Filtering based on each stellar object's parameters for", target_types, logic_str)
        for single_star in self:
            available_object_parameters = single_star.params.available_params
            target_found_flag = core_filter(and_logic_for_multiples, target_types, available_object_parameters)
            if not (target_found_flag and not keep_compliment):
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed)
            if self.star_names == set():
                print("    'filter_by_object_parameters' has ended with and empty set of data.")

    def filter_by_object_name_types(self, and_logic_for_multiples, target_types, keep_compliment=False):
        stars_removed = 0
        target_types = set(target_types)
        if self.verbose:
            if and_logic_for_multiples:
                logic_str = "using 'And' logic."
            else:
                logic_str = "using 'Or' logic."
            print("Filtering on each stellar object's available name types", target_types, logic_str)
        for single_star in self:
            available_star_name_types = set(single_star.star_names_dict.keys())
            target_found_flag = core_filter(and_logic_for_multiples, target_types, available_star_name_types)
            if not (target_found_flag and not keep_compliment):
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed)
            if self.star_names == set():
                print("   'filter_by_object_name_types' has ended with and empty set of data.")

    def match_filter_for_object_parameters(self, targets, keep_compliment=False):
        stars_removed = 0
        target_types = {target.lower() for target, match_values in targets}
        # filter the data to have all the required target types.
        self.filter_by_object_parameters(and_logic_for_multiples=True, target_types=target_types,
                                         keep_compliment=keep_compliment)
        # The match filter
        for target, match_values in targets:
            target = target.lower()
            if self.verbose:
                print("Match filtering for object parameters for the parameter:")
                print(" ", target, "target values of", match_values, ".")
            for single_star in self:
                if target == "sptype":
                    value = single_star.params.spyype.value[0]
                else:
                    value = single_star.params.__getattribute__(target).value
                if not (value in match_values and not keep_compliment):
                    stars_removed += 1
                    self.__delattr__(single_star.attr_name)
                    self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed)
            if self.star_names == set():
                print("    'match_filter_for_object_parameters' has ended with and empty set of data.")

    def bound_filter_for_object_parameters(self, targets, keep_compliment=False):
        stars_removed = 0
        target_types = {target.lower() for target, lower_bound, upper_bound in targets}
        # filter the data to have all the required target types.
        self.filter_by_object_parameters(and_logic_for_multiples=True, target_types=target_types,
                                         keep_compliment=keep_compliment)
        # The bound filter
        for target, lower_bound, upper_bound in targets:
            target = target.lower()
            if self.verbose:
                print("Bound filtering in the stellar object parameters for the parameter:")
                print(" ", target, "for a lower bound of", lower_bound, "and an upper bound of", upper_bound, ".")
            for single_star in self:
                below_upper = True
                these_params = single_star.params
                this_single_param = these_params.__getattribute__(target)
                if upper_bound is not None:
                    if this_single_param.value >= upper_bound:
                        below_upper = False
                above_lower = True
                if lower_bound is not None:
                    if this_single_param.value < lower_bound:
                        above_lower = False
                if not (above_lower and below_upper and not keep_compliment):
                    stars_removed += 1
                    self.__delattr__(single_star.attr_name)
                    self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed)
            if self.star_names == set():
                print("    'bound_filter_for_object_parameters' has ended with and empty set of data.")

    def filter_by_available_abundances(self, and_logic_for_multiples, target_types):
        catalogs_removed = 0
        stars_removed = 0
        target_types = set(target_types)
        if self.verbose:
            if and_logic_for_multiples:
                logic_str = "using 'And' logic."
            else:
                logic_str = "using 'Or' logic."
            print("Filtering by the elements:", target_types, logic_str)
        for single_star in self:
            an_element_found_this_star = False
            elements_not_found_this_star = target_types
            for short_catalog_name in list(single_star.available_abundance_catalogs):
                an_element_found_this_catalog = False
                elements_this_catalog = single_star.__getattribute__(short_catalog_name).available_abundances
                elements_not_found_this_star = elements_not_found_this_star - elements_this_catalog
                if elements_this_catalog & target_types != set():
                    an_element_found_this_catalog = True
                    an_element_found_this_star = True
                if not an_element_found_this_catalog:
                    catalogs_removed += 1
                    single_star.__delattr__(short_catalog_name)
                    single_star.available_abundance_catalogs.remove(short_catalog_name)
                    try:
                        single_star.available_data_types.remove(short_catalog_name)
                    except KeyError:
                        pass
            if not an_element_found_this_star or (and_logic_for_multiples and elements_not_found_this_star != set()):
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed, "  Catalogs removed:", catalogs_removed)
            if self.star_names == set():
                print("    'filter_by_available_abundances' has ended with and empty set of data.")

    def bound_filter_for_elements(self, targets):
        catalogs_removed = 0
        stars_removed = 0
        targets = set(targets)
        elements = {element for element, upper, lower in targets}
        if self.verbose:
            print("Bound filtering by elements (element, lower bound, upper bound):", targets)
        for single_star in self:
            bounds_satisfied_at_least_one_catalog = False
            elements_not_found_this_star = set(elements)
            for short_catalog_name in list(single_star.available_abundance_catalogs):
                single_catalog = single_star.__getattribute__(short_catalog_name)
                elements_this_catalog = single_catalog.available_abundances
                elements_not_found_this_star = elements_not_found_this_star - elements_this_catalog
                for element, lower, upper in targets:
                    if element in elements_this_catalog:
                        value = single_catalog.__getattribute__(element)
                        if lower <= value <= upper:
                            pass
                        else:
                            all_values_in_bounds = False
                            break
                    else:
                        all_values_in_bounds = False
                        break
                else:
                    all_values_in_bounds = True
                    bounds_satisfied_at_least_one_catalog = True
                if not all_values_in_bounds:
                    catalogs_removed += 1
                    single_star.__delattr__(short_catalog_name)
                    single_star.available_abundance_catalogs.remove(short_catalog_name)
                    try:
                        single_star.available_data_types.remove(short_catalog_name)
                    except KeyError:
                        pass
            if not bounds_satisfied_at_least_one_catalog:
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed, "  Catalogs removed:", catalogs_removed)
            if self.star_names == set():
                print("    'bound_filter_for_elements' has ended with and empty set of data.")

    def min_abundance_check(self):
        """
        This will make sure that every catalog with abundance measurements has at least the element has iron (Fe) and
        and one other element that is not iron. {Fe, FeII} is filtered away, but {FeII, Li} is retained.

        :return:
        """
        catalogs_removed = 0
        stars_removed = 0
        if self.verbose:
            print("Filtering out catalogs that do not have iron and at least one other non-iron element.")
        for single_star in self:
            min_requirements_this_star = False
            for short_catalog_name in list(single_star.available_abundance_catalogs):
                elements_this_catalog = single_star.__getattribute__(short_catalog_name).available_abundances
                if self.iron_el in elements_this_catalog and elements_this_catalog - self.iron_set != set():
                    min_requirements_this_star = True
                else:
                    catalogs_removed += 1
                    single_star.__delattr__(short_catalog_name)
                    single_star.available_abundance_catalogs.remove(short_catalog_name)
                    single_star.available_data_types.remove(short_catalog_name)
            if not min_requirements_this_star:
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed, "  Catalogs removed:", catalogs_removed)
            if self.star_names == set():
                print("    min_abundance_check has ended with and empty set of data.")

    def remove_nlte(self):
        catalogs_removed = 0
        stars_removed = 0
        if self.verbose:
            print("Removing NLTE elements.")
        for single_star in self:
            an_element_found_this_star = False
            for short_catalog_name in list(single_star.available_abundance_catalogs):
                an_element_found_this_catalog = False
                this_catalog = single_star.__getattribute__(short_catalog_name)
                elements_this_catalog = this_catalog.available_abundances
                nlte_abundances = {abundance for abundance in elements_this_catalog if abundance.is_nlte}
                for nlte_abundance in nlte_abundances:
                    this_catalog.__delattr__(str(nlte_abundance))
                    this_catalog.available_abundances.remove(nlte_abundance)
                if set() != elements_this_catalog - nlte_abundances:
                    an_element_found_this_catalog = True
                if an_element_found_this_catalog:
                    an_element_found_this_star = True
                else:
                    catalogs_removed += 1
                    single_star.__delattr__(short_catalog_name)
                    single_star.available_abundance_catalogs.remove(short_catalog_name)
                    try:
                        single_star.available_data_types.remove(short_catalog_name)
                    except KeyError:
                        pass
            if not an_element_found_this_star:
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(single_star.star_reference_name)
        if self.verbose:
            print("  Stars removed:", stars_removed, "  Catalogs removed:", catalogs_removed)
            if self.star_names == set():
                print("    remove_nlte is returning an empty set of data.")

    def remove_non_targets(self, matching_truth_value):
        stars_removed = 0
        if self.verbose:
            print("Removing not target star.")
        for hypatia_handle in list(self.star_names):
            single_star = self.__getattribute__(hypatia_handle)
            if matching_truth_value != single_star.is_target:
                stars_removed += 1
                self.__delattr__(single_star.attr_name)
                self.star_names.remove(hypatia_handle)
        if self.verbose:
            print("  Stars removed:", stars_removed)
            if self.star_names == set():
                print("    remove_non_targets is returning an empty set of data.")

    def filter(self, target_catalogs=None, or_logic_for_catalogs=True,
               catalogs_return_only_targets=False,
               target_star_name_types=None, and_logic_for_star_names=True,
               target_params=None, and_logic_for_params=True,
               target_elements=None, or_logic_for_element=True,
               element_bound_filter=None,
               min_catalog_count=None,
               parameter_bound_filter=None,
               parameter_match_filter=None,
               has_exoplanet=None,
               at_least_fe_and_another=False,
               remove_nlte_abundances=False,
               is_target=None,
               keep_complement=False):
        """
            Filtering of the Hypatia Catalog Data. 'And' logic is used when multiple filters are employed, meaning a
            single star must pass all filters to be included in the target star_data, All data that that does not pass
            the filter to be in the target star data is added to the complement_data.

        :param target_catalogs: None or set. To filter based on catalog name(s). This input should be a list with
                                elements that are a string of a single catalog name. See self.init_catalogs for options.
                                The default value is None, indicating that no filtering should occur.
        :param or_logic_for_catalogs: bool. Default value is True. When True, a Hypatia star can contain any of the
                                      catalogs listed in the keyword argument target_catalogs. When False, a Hypatia
                                      star must contain data from all the catalogs in target_catalogs.
        :param catalogs_return_only_targets: bool. Default value is False. When True this deletes all the abundance
                                             catalogs that are not the target_catalogs.
        :param target_star_name_types: None or set. To filter based on available star name types. This input should be
                                       a list with element that are strings equal to the star name types. Examples can
                                       be found from hypatia.load.star_names import star_name_types. The default value
                                       is None, indicating that no filtering should occur.
        :param and_logic_for_star_names: bool. Default value is True. When True, a Hypatia star must contain all of the
                                         star_names listed in the keyword argument target_star_name_types. When False, a
                                         Hypatia star may contain data from any the catalogs in target_star_name_types.
        :param target_params: None or set. To filter based on a Hypatia star's stellar parameters, listed under the
                              'params' key in the star's dictionary. This input should be a list with elements that are
                              a string of a single stellar parameter. These parameters are set in this class under the
                              various methods that end in "_params". The default value is None, indicating that no
                              filtering should occur.
        :param and_logic_for_params: bool. Default value is True. When True, a Hypatia star must contain all of the
                                           parameters listed in the keyword argument target_params. When False, a
                                           Hypatia star may contain parameters from any the catalogs in target_params.
        :param target_elements: None or set. To filter based on a Hypatia star's elemental abundances, listed under the
                                a key that is based on the catalog names for that abundance data. The user does not need
                                to specify the catalog name in the star's dictionary. This input should be a set, the
                                elements of that set, should be elemental abbreviations for the Elements of the
                                Periodic Table. These abbreviations are available from hypatia.tool.elements import
                                element_dict and the call element_dict.keys(). The default value is None, indicating
                                that no filtering should occur. Catalogs with no matching elements are removed.
        :param or_logic_for_element: bool. Default value is True. When True, a Hypatia star can contain any of the
                                     elemental abundances listed in the keyword argument target_elements. When False, a
                                     Hypatia star must contain data from all elemental abundances in target_elements.
                                     Catalogs with no matching elements are removed.
        :param element_bound_filter: None or set. First this filters based on a Hypatia star's elemental abundances
                                     listed under the a key that is based on the catalog names for that abundance data.
                                     Second this filters based on the the upper and lower bounds the are requested for
                                     this parameter. The input should be a set of tuples that are of the form
                                     (element, lower_bound, upper_bound). upper and lower bound should be a float or
                                     None (indicating no bound). A star is included to the target data set if
                                     lower_bound <= star_data[star_name]['params'][parameter_type] < upper_bound.
                                     The default value is None, indicating that no filtering should occur.
        :param min_catalog_count: None or int. An integer indicating the minimum number of stellar abundance catalogs
                                  that each Hypatia star must contain. The default value is None, indicating that no
                                  filtering should occur.
        :param parameter_bound_filter: None or set. First this filters based on a Hypatia star's stellar parameters,
                                       listed under the 'params' key in the star's dictionary. Second this filters based
                                       on the the upper and lower bounds the are requested for this parameter. The input
                                       should be a list with elements that tuples of the form
                                       (parameter_type, lower_bound, upper_bound). upper and lower bound should be a
                                       float or None (indicating no bound). A star is included to the target data set if
                                       lower_bound <= star_data[star_name]['params'][parameter_type] < upper_bound.
                                       The default value is None, indicating that no filtering should occur.
        :param parameter_match_filter: None or set. First this filters based on a Hypatia star's stellar parameters,
                                       listed under the 'params' key in the star's dictionary. Second this filters based
                                       on if the targeted parameter matches a set of desired values. The input should be
                                       a list with elements that are tuples of the form (parameter_type, match_values).
                                       A star is included to the target data set if
                                       star_data[star_name]['params'][parameter_type] in match_value, where match values
                                       is a set of acceptable values. The default value is None, indicating that no
                                       filtering should occur.
        :param has_exoplanet: bool or None. If None, no filtering occurs. If True, data with the the elements of
                              self.star_data with the 'exo' keyword are selected for the output (elements of
                              self.star_data that have exoplanets). If False, elements with no exoplanet data are
                              selected for the target_data
        :param remove_nlte_abundances: bool. If True, any elemental abundance with NLTE is removed. Default setting is
                                       False, which does no filtering.
        :param at_least_fe_and_another: bool. If True, catalogs that do not contain iron and at least one other
                                        non-iron element are removed. Default setting is False, which does no filtering.
        :param keep_complement: bool. If True, the compliment of the filtering targets is saved instead of the
                                targets to self.output_star_data.
        :param is_target: None or bool. None skips this filter. If True, select SingleStar instances with the attribute
                                        is_target==True, and False selects SingleStar instances where is_target==False.
        :return: self.output_star_data
        """
        if has_exoplanet is not None:
            self.filter_by_available_data_type(and_logic_for_multiples=True, target_types={'exo'},
                                               keep_compliment=keep_complement)
        if target_catalogs is not None:
            self.filter_by_available_data_type(and_logic_for_multiples=not or_logic_for_catalogs,
                                               target_types=target_catalogs,
                                               return_only_targets=catalogs_return_only_targets,
                                               keep_compliment=keep_complement)
        if min_catalog_count is not None:
            self.filter_by_min_cat_count(minimum_cat_count=min_catalog_count, keep_compliment=keep_complement)
        if target_params is not None:
            self.filter_by_object_parameters(and_logic_for_multiples=and_logic_for_params,
                                             target_types=target_params, keep_compliment=keep_complement)
        if target_star_name_types is not None:
            self.filter_by_object_name_types(and_logic_for_multiples=and_logic_for_star_names,
                                             target_types=target_star_name_types, keep_compliment=keep_complement)
        if parameter_match_filter is not None:
            self.match_filter_for_object_parameters(targets=parameter_match_filter, keep_compliment=keep_complement)
        if parameter_bound_filter is not None:
            self.bound_filter_for_object_parameters(targets=parameter_bound_filter, keep_compliment=keep_complement)
        if target_elements is not None:
            self.filter_by_available_abundances(and_logic_for_multiples=not or_logic_for_element,
                                                target_types=target_elements)
        if element_bound_filter is not None:
            self.bound_filter_for_elements(targets=element_bound_filter)
        if remove_nlte_abundances:
            self.remove_nlte()
        if at_least_fe_and_another:
            self.min_abundance_check()
        if is_target is not None:
            self.remove_non_targets(matching_truth_value=is_target)
        if self.verbose:
            print("Filtering complete.\n")

    def normalize(self, norm_keys: list[str] = None):
        """
        Set the solar normalization for all the data in this class.

        :param norm_keys: list[str]
                        If norm_key='original', then a special procedure
                               is preformed to make individual catalogs revert back
                               to their original normalization. Otherwise the same
                               normalization is applied across all catalogs. This results,
                               in a loss of data for elements that reported in the catalog
                               as "absolute".
        :return:
        """
        if norm_keys is None:
            norm_keys = ['original']
        for norm_key in norm_keys:
            if self.verbose:
                print(f"Normalizing abundance data using the {norm_key} solar normalization for all data.")
            for single_star in self:
                for catalog_short_name in list(single_star.available_abundance_catalogs):
                    this_catalog = single_star.__getattribute__(catalog_short_name)
                    this_catalog.normalize(norm_key)
            self.data_norms.add(norm_key)
            if self.verbose:
                print("  Normalization complete.\n")

    def get_element_ratio_and_distance(self, element_set=None,
                                       distance_list=None, xlimits_list=None, ylimits_list=None,
                                       has_exoplanet=None, use_median=True):
        if distance_list is None:
            distance_list = self.distance_bin_default
        if self.stats is None:
            self.do_stats()
        if element_set is None:
            element_set = set(self.stats.element_count.keys()) - {"Fe"}
        if self.verbose:
            print("Starting Element Ratio and Distance Plots... \n")
            print(len(element_set), "elements are being plotted.")
        for element in element_set:
            if self.verbose:
                print(element, " is starting")
            x_label = "[Fe/H]"
            y_label = "[" + element + "/Fe]"
            figname = element + "FevsFeH"
            data_list = []
            label_list = []
            for distance_index in range(len(distance_list) - 1):
                x_data = []
                y_data = []
                lower_bound = distance_list[distance_index]
                upper_bound = distance_list[distance_index + 1]
                label_list.append(str(lower_bound) + " ≤ d < " + str(upper_bound))
                temp_output_star_data = OutputStarData()
                temp_output_star_data.receive_data(star_data=self)
                temp_output_star_data.filter(target_elements=[element],
                                             parameter_bound_filter=[('dist', lower_bound, upper_bound)],
                                             has_exoplanet=has_exoplanet)
                for star_name in temp_output_star_data.star_names:
                    simbad_doc = get_star_data(star_name, test_origin="OutputStarData")
                    attr_name = simbad_doc['attr_name']
                    reduced_data_this_star = temp_output_star_data.__getattribute__(attr_name).reduced_abundances
                    if use_median:
                        iron_value = reduced_data_this_star.Fe.median
                        y_data.append(reduced_data_this_star.__getattribute__(element).median - iron_value)
                        x_data.append(iron_value)
                    else:
                        iron_value = reduced_data_this_star.Fe.mean
                        y_data.append(reduced_data_this_star.__getattribute__(element).mean - iron_value)
                        x_data.append(iron_value)
                data_list.append((x_data, y_data))
            make_element_distance_plots(distance_abundance_data=data_list, xlimits=xlimits_list, ylimits=ylimits_list,
                                        label_list=label_list, xlabel=x_label, ylabel=y_label, figname=figname,
                                        save_figure=True, do_eps=False, do_pdf=True, do_png=False)
        if self.verbose:
            print("  ...Element Ratio and Distance Plots completed \n")

    def export_to_mongo(self, catalogs_file_name: str = default_catalog_file):
        hypatia_db = HypatiaDB(db_name=MONGO_DATABASE, collection_name='hypatiaDB')
        hypatia_db.reset()
        for single_star in self:
            available_params = single_star.params.available_params
            if 'sptype' in available_params:
                sptype_param = single_star.params.sptype
                new_param = SingleParam.strict_format(param_name='sptype_num',
                                                      value=spectral_type_to_float(single_star.params.sptype.value),
                                                      ref=sptype_param.ref,
                                                      units='')
                single_star.params.update_param('sptype_num', new_param)
            if 'disk' in available_params:
                disk_param = single_star.params.disk
                disk_num = None
                if disk_param.value == 'thin':
                    disk_num = 0
                elif disk_param.value == 'thick':
                    disk_num = 1
                elif disk_param.value == 'N/A':
                    pass
                else:
                    raise ValueError("Disk value not recognized.")
                if disk_num is not None:
                    new_param = SingleParam.strict_format(param_name='disk_num',
                                                          value=disk_num,
                                                          ref=disk_param.ref,
                                                          units='')
                    single_star.params.update_param('disk_num', new_param)
            hypatia_db.add_star(single_star)
        # add the summary and site-wide information
        found_elements = hypatia_db.added_elements
        found_element_nlte = hypatia_db.added_elements_nlte
        found_catalogs = hypatia_db.added_catalogs
        found_normalizations = hypatia_db.added_normalizations
        ids_with_wds_names = set(hypatia_db.get_ids_for_name_type('wds'))
        ids_with_nea_names = set(hypatia_db.get_ids_for_nea())
        upload_summary(found_elements=found_elements, found_element_nlte=found_element_nlte,
                       catalogs_file_name=catalogs_file_name, found_catalogs=found_catalogs,
                       found_normalizations=found_normalizations,
                       ids_with_wds_names=ids_with_wds_names, ids_with_nea_names=ids_with_nea_names)
