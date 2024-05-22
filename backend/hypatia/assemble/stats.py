import os

import numpy as np
import matplotlib.pyplot as plt

from hypatia.config import working_dir
from hypatia.sources.elements import element_rank
from hypatia.object_params import params_err_format
from hypatia.sources.simbad.ops import get_star_data
from hypatia.sources.simbad.db import indexed_name_types
from hypatia.assemble.site.chemistry import get_representative_error


def autolabel(rects):
    """
    attach some text labels
    """
    for rect in rects:
        height = rect.get_height()
        if height < 300 and not height==0.:
            height1 = height #+20.
        else:
            height1 = height
        plt.text(rect.get_x()+rect.get_width()/2., 1.02*height1, '%d'%int(height),
                 ha='center', va='bottom')


class ElementStats:
    def __init__(self, element_name):
        self.name = element_name
        self.value_list = []
        self.catalog_list = []
        self.catalogs = {}
        self.len = 0
        self.mean = self.median = self.max = self.min = self.spread = self.plusminus = self.std = None

    def add_value(self, value: float, catalog: str):
        formatted_value = np.around(float(value), decimals=3)
        self.value_list.append(formatted_value)
        self.catalog_list.append(catalog)
        self.catalogs[catalog] = formatted_value

    def calc_stats(self):
        self.len = self.__len__()
        if self.len < 1:
            pass
        elif self.len < 2:
            self.mean = self.median = self.max = self.min = self.value_list[0]
        else:
            self.mean = np.around(np.mean(self.value_list), decimals=3)
            self.median = np.around(np.median(self.value_list), decimals=3)
            self.max = np.max(self.value_list)
            self.min = np.min(self.value_list)
            self.spread = np.around(self.max - self.min, decimals=3)
            self.plusminus = np.around(self.spread / 2.0, decimals=2)
            if self.len > 2:
                self.std = params_err_format(np.std(self.value_list), sig_figs=3)
        if self.plusminus is None or self.plusminus == 0.0:
            self.plusminus = get_representative_error(element_name=self.name)

    def __len__(self):
        return len(self.value_list)

    def __getitem__(self, item):
        return self.__getattribute__(item)


class CountPerBin:
    def __init__(self, thing_counted, bin):
        self.description = "The counted number of " + str(thing_counted) +\
                          " for a each " + str(bin) +\
                          " type that has at least 1 " + str(bin) + " of that type."
        self.available_bins = set()

    def count_bins(self, bins):
        for one_bin in bins:
            if one_bin in self.available_bins:
                self.__setattr__(one_bin, self.__getattribute__(one_bin) + 1)
            else:
                self.__setattr__(one_bin, 1)
                self.available_bins.add(one_bin)

# To run this in the terminal: stats.star_count_per_element.extra_special_nat_histogram()
    def extra_special_nat_histogram(self):
        n = len(self.available_bins) + 1
        ordered_list_of_bins = [""]
        if "each elemental abundance" in self.description:
            ordered_list_of_bins.extend(sorted(self.available_bins, key=element_rank))
        else:
            ordered_list_of_bins.extend(sorted(self.available_bins))
        hits = [0]
        hits.extend([self.__getattribute__(bin_name) for bin_name in ordered_list_of_bins[1:]])
        ind = np.arange(n)
        width = 0.6
        fig = plt.figure(figsize=(22,5))
        ax = fig.add_subplot(111)
        rects1 = plt.bar(ind, hits, width, color='#4E11B7')
        ax.set_xlabel('Element Abundances in the Hypatia Catalog', fontsize=15)
        ax.set_ylabel('Number of Stars with Measured Element X', fontsize=15)
        ax.set_ylim([0.0, np.max(hits) +600.])
        ax.set_xlim([0.0, float(n + 1)])
        ax.set_xticks(ind)
        ax.set_xticklabels(tuple(ordered_list_of_bins))
        ax.text(50, 9000, "FGKM-type Stars Within 500pc: "+str(np.max(hits)), fontsize=20,  fontweight='bold', color='#4E11B7')
        ax.text(50, 8000, "Literature Sources: +230", fontsize=20,  fontweight='bold', color='#4E11B7')
        ax.text(50, 7000, "Number of Elements/Species: "+str(len(ordered_list_of_bins)-1), fontsize=20,  fontweight='bold', color='#4E11B7')
        autolabel(rects1)
        #plt.title(self.description)
        #ax.show()
        ax.set_aspect('auto')
        name="bigHist-"+str(np.max(hits))+".pdf"
        file_name = os.path.join(working_dir, "plots", 'output', "hist", name)
        fig.savefig(file_name)
        print("Number of elements", len(ordered_list_of_bins)-1)
        return ordered_list_of_bins


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


class ReducedAbundances:
    def __init__(self):
        self.available_abundances = set()

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def add_abundance(self, abundance_record, element_name, catalog):
        if element_name not in self.available_abundances:
            self.__setattr__(element_name, ElementStats(element_name))
            self.available_abundances.add(element_name)
        self.__getattribute__(element_name).add_value(abundance_record, catalog)

    def calc(self):
        [self.__getattribute__(element_name).calc_stats() for element_name in self.available_abundances]
