"""
Nat's Test Space

The current code below takes the input file (no spaces between commas, often a "planets_" file from NEA)
and creates a mini-sources by matching only to those stars while still retaining all of the tools and
stats of the main Hypatia sources. To execute, run this file in the terminal. Might need to move this to
standard_lib at some point.
"""
import os

import numpy as np
import matplotlib.pyplot as plt

from hypatia.plots.histograms import autolabel
from hypatia.plots.histograms import get_hist_bins
from hypatia.configs.file_paths import histo_dir

def mdwarf_histogram(self):
    ordered_list_of_bins = get_hist_bins(available_bins=self.available_bins,
                                         is_element_id="each elemental abundance" in self.description)
    if 'Fe' in ordered_list_of_bins:
        ordered_list_of_bins.remove('Fe')
    hits = [0]
    hits.extend([self.__getattribute__(bin_name) for bin_name in ordered_list_of_bins[1:]])
    ordered_list_of_bins.insert(2, '13C')
    hits.insert(2, 2)
    ordered_list_of_bins.insert(5, 'F')
    hits.insert(5, 0)
    ordered_list_of_bins.remove('NLTE_Sr_II')
    hits.pop(-2)
    print(ordered_list_of_bins)
    print(hits)
    baseline_hits = [0, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    threshold_hits = [0, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 125, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    base_plus_hits = [sum(x) for x in zip(baseline_hits, hits)]
    thresh_plus_hits = [sum(x) for x in zip(threshold_hits, hits)]
    ind = np.arange(len(ordered_list_of_bins))/1.4
    width = 0.65
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)
    total_num = self.__getattribute__('Fe')
    rects_base = plt.bar(ind, base_plus_hits, width, color='firebrick', label="SAKHMET Expected Mission")
    rects_thresh = plt.bar(ind, thresh_plus_hits, width, color='salmon', label="Required Mission")
    rects_data = plt.bar(ind, hits, width, color="grey", label="Current M-dwarf Data")
    ax.set_xlabel('Spectroscopic Abundances for M-Dwarfs (excluding Fe)', fontsize=15)
    ax.set_ylabel('Number of Stars with Measured Element X', fontsize=14)
    ax.set_ylim([0.0, np.max(baseline_hits) + 650.])
    ax.set_xlim([0.0, float(len(ordered_list_of_bins))])
    ax.set_xticks(ind)
    ax.set_xticklabels(tuple([name.replace('_', '') for name in ordered_list_of_bins]), fontsize=13)
    ax.legend(loc='upper left', scatterpoints=1, fontsize=12)
    #ax.text(50, 9000, "FGKM-type Stars Within 500pc: " + str(np.max(hits)), fontsize=20, fontweight='bold',
    #        color='#4E11B7')
    #ax.text(50, 8000, "Literature Sources: +230", fontsize=20, fontweight='bold', color='#4E11B7')
    #ax.text(50, 7000, "Number of Elements/Species: " + str(len(ordered_list_of_bins) - 1), fontsize=20,
    #       fontweight='bold', color='#4E11B7')
    autolabel(rects_data)
    # plt.title(self.description)
    # ax.show()
    ax.set_aspect('auto')
    name = "mdwarf24-bigHist-" + str(total_num) + ".pdf"
    file_name = os.path.join(histo_dir, name)
    fig.savefig(file_name)
    print("Number of elements", len(ordered_list_of_bins))
    return ordered_list_of_bins #, rects_base, rects_thresh

#mdwarf_histogram(stats.star_count_per_element)
# Note to self: To run this, run directly in a Python terminal
