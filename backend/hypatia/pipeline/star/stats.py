from hypatia.elements import ElementID
from hypatia.sources.simbad.ops import get_star_data
from hypatia.sources.simbad.db import indexed_name_types


class CountPerBin:
    def __init__(self, thing_counted, bin):
        self.description = "The counted number of " + str(thing_counted) +\
                          " for a each " + str(bin) +\
                          " type that has at least 1 " + str(bin) + " of that type."
        self.available_bins = set()

    def count_bins(self, bins):
        for one_bin in bins:
            if isinstance(one_bin, ElementID):
                bin_name = str(one_bin)
            else:
                bin_name = one_bin
            if one_bin in self.available_bins:
                self.__setattr__(bin_name, self.__getattribute__(bin_name) + 1)
            else:
                self.__setattr__(bin_name, 1)
                self.available_bins.add(one_bin)


class StarDataStats:
    def __init__(self, star_data, params_set=None, star_name_types=None):
        if params_set is None:
            params_set = set()
        else:
            params_set = set(params_set)
        if star_name_types is None:
            star_name_types = set(indexed_name_types)
        else:
            star_name_types = set(star_name_types)

        self.star_count = 0
        self.stars_with_exoplanets = 0
        self.element_count_per_catalog_per_star = CountPerBin(thing_counted="catalogs within each star",
                                                              bin='elemental abundance')
        self.star_count_per_stellar_param = CountPerBin(thing_counted="stars", bin='stellar parameters')
        self.star_count_per_element = CountPerBin(thing_counted="stars", bin='elemental abundance')
        self.star_count_per_star_type = CountPerBin(thing_counted="stars", bin='found star name type')
        for stellar_param in params_set:
            self.__setattr__("stellar_param_" + str(stellar_param) + "_count_per_element",
                             CountPerBin(thing_counted="stellar parameter " + str(stellar_param),
                             bin="elemental abundance"))
        for star_name_type in star_name_types:
            self.__setattr__("star_type_" + str(star_name_type + "_count_per_element"),
                             CountPerBin(thing_counted="star_name type: " + str(star_name_type),
                             bin="elemental abundance"))
        self.norm_count_per_element = {}
        self.norm_count_per_star = {}
        # - {"catalog", "#ref"}
        for star_name in star_data.star_names:
            simbad_doc = get_star_data(star_name, test_origin="StarDataStats")
            single_star = star_data.__getattribute__(simbad_doc['attr_name'])
            # count for the number of stars
            self.star_count += 1
            # stars with exoplanets
            if 'exo' in single_star.available_data_types:
                self.stars_with_exoplanets += 1
            # counts of stars per abundance
            abundances_this_star = set()
            for catalog in single_star.available_abundance_catalogs:
                available_abundances_this_catalog = single_star.__getattribute__(catalog).available_abundances
                self.element_count_per_catalog_per_star.count_bins(available_abundances_this_catalog)
                abundances_this_star = abundances_this_star | available_abundances_this_catalog
            self.star_count_per_element.count_bins(abundances_this_star)
            # counts of stars per stellar parameter
            param_overlap = params_set & single_star.params.available_params
            self.star_count_per_stellar_param.count_bins(param_overlap)
            for stellar_param in param_overlap:
                self.__getattribute__("stellar_param_" + str(stellar_param) + "_count_per_element")\
                    .count_bins(abundances_this_star)
            # counts of stars per stellar name type
            name_type_overlap = star_name_types & single_star.available_star_name_types
            self.star_count_per_star_type.count_bins(name_type_overlap)
            for star_name_type in name_type_overlap:
                self.__getattribute__("star_type_" + str(star_name_type + "_count_per_element"))\
                    .count_bins(abundances_this_star)
