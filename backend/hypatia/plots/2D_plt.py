import os
import statistics
from matplotlib.colors import LinearSegmentedColormap
import sys
from collections import Counter

import matplotlib as mpl
from django.template.defaulttags import widthratio
import numpy as np
import math

if sys.platform == 'darwin':
    mpl.use(backend='MACOSX')
else:
    mpl.use(backend='TkAgg')
from matplotlib import pyplot as plt

from hypatia.configs.file_paths import plot_dir
from hypatia.tools.web_query import get_graph_data


"""
See more input parameter options at https://hypatiacatalog.com/api under the section `GET data`.
"""
colors = [
    '#4e11b7',  # hypatia purple
    '#6c5ce7',  # vibrant indigo
    '#dfe6e9',  # neutral white-silver
    '#81ecec',  # aqua
    '#92F7B0',  # mint green
    '#F7C492',  # coral
    '#d63031',  # strong red

]

element_err = {
    "Ag": 0.2,
    "Al": 0.06,
    "Ba_II": 0.19,
    "Be": 0.12,
    "C": 0.09,
    "Ca": 0.06,
    "Ca_II": 0.03,
    "Ce": 0.076,
    "Ce_II": 0.07,
    "Co": 0.04,
    "Cr": 0.045,
    "Cr_II": 0.066,
    "Cu": 0.08,
    "Dy": 0.4,
    "Dy_II": 0.11,
    "Er_II": 0.16,
    "Eu": 0.11,
    "Eu_II": 0.1,
    "Fe": 0.04,
    "Gd": 0.6,
    "Gd_II": 0.13,
    "Hf": 0.2,
    "Hf_II": 0.18,
    "K": 0.04,
    "La": 0.086,
    "La_II": 0.22,
    "Li": 0.1,
    "Mg": 0.07,
    "Mn": 0.056,
    "Mo": 0.12,
    "N": 0.11,
    "Na": 0.04,
    "Nb_II": 0.15,
    "Nd": 0.07,
    "Ni": 0.05,
    "O": 0.09,
    "P": 0.04,
    "Pb": 0.22,
    "Pd": 0.19,
    "Pr": 0.13,
    "Pr_II": 0.1,
    "Ru": 0.12,
    "S": 0.09,
    "Sc": 0.05,
    "Sc_II": 0.09,
    "Si": 0.05,
    "Sm": 0.07,
    "Sm_II": 0.155,
    "Sr": 0.106,
    "Sr_II": 0.15,
    "Tb_II": 0.11,
    "Th_II": 0.14,
    "Ti": 0.05,
    "Ti_II": 0.06,
    "Tm_II": 0.2,
    "V": 0.07,
    "V_II": 0.105,
    "Y": 0.085,
    "Y_II": 0.08,
    "Yb_II": 0.14,
    "Zn": 0.076,
    "Zr": 0.1,
    "Zr_II": 0.08,
    "F": 0.12,
    "Si_II": 0.05,
    "Cl": 0.23,
    "Mn_II": 0.056,
    "Rb": 99.99,
    "Sn": 99.99,
    "Ba": 0.15,
    "Ir": 0.28,
    "Nd_II": 0.07,
    "H": 0.0
}

hypatia_colormap = LinearSegmentedColormap.from_list("hypatia_colormap", colors)

xaxis1 = 'Fe'
xaxis2 = 'H'
yaxis1 = 'N'
yaxis2 = 'H'
plot_data = get_graph_data(xaxis1=xaxis1, xaxis2=xaxis2, yaxis1=yaxis1, yaxis2=yaxis2)
if plot_data is not None:
    fig, ax = plt.subplots()
    x_handle = f'{xaxis1}'
    if xaxis2 is not None and xaxis2.lower()!= 'h':
        x_handle += f'_{xaxis2}'
    y_handle = f'{yaxis1}'
    if yaxis2 is not None and yaxis2.lower()!= 'h':
        y_handle += f'_{yaxis2}'
    #for both hist and heat
    hist = True
    heat = False
    both = False


    full_data = False
    stand_dev = False
    sigma = 3
    per_max = True
    percent = 30
    over_ride = False
    maximum = 0.85
    minimum = -0.45
    data = plot_data[x_handle]

    #specifically for heat
    width_x = 2 * element_err[xaxis1]
    width_y = 2 * element_err[yaxis1]
    minimum_y = 0.8
    minimum_x = 0.8
    maximum_y = 0.95
    maximum_x = 0.95


    if hist is True:
        if data is plot_data[x_handle]:
            ax.set_xlabel(f'[{xaxis1}/{xaxis2}]')
            width = 2 * math.log(10) * math.sqrt((element_err[xaxis1] ** 2) + (element_err[xaxis2] ** 2))
        else:
            ax.set_xlabel(f'[{yaxis1}/{yaxis2}]')
            width = 2 * math.log(10) * math.sqrt((element_err[yaxis1] ** 2) + (element_err[yaxis2] ** 2))

        if full_data is True:
            bins = round((abs(min(data) + abs(max(data))) / width))
            range_min = (min(data))
            range_max = (max(data))

        elif stand_dev is True:
            mean = statistics.mean(data)
            stdev = statistics.stdev(data)
            threshold = sigma*stdev
            range_min = mean-threshold
            range_max = mean+threshold
            bins = round((abs(range_min)+abs(range_max))/width)

        elif per_max is True:
            bins_init = round((abs(min(data))/width))
            hist = np.histogram(data, bins=bins_init)
            norm_hist = hist[0]/max(hist[0])
            bin_edges_init = hist[1]
            threshold = percent*0.01
            keep_bin_indices = np.where(norm_hist >= threshold)[0] #identify the indices to keep
            bin_edges = bin_edges_init[keep_bin_indices]
            bin_edges_upper = bin_edges_init[keep_bin_indices + 1]
            filtered_data = []
            for lower, upper in zip(bin_edges, bin_edges_upper):
                filtered_data.extend([x for x in data if lower <= x < upper])
            filtered_data = np.array(filtered_data)
            data = filtered_data
            range_min = filtered_data.min()
            range_max = filtered_data.max()
            bins = round((abs(range_min)+abs(range_max))/width)

        elif over_ride is True:
            bins = round((abs(minimum)+abs(maximum))/width)
            range_min = minimum
            range_max = maximum

        ax.hist(data, bins=bins, edgecolor='black', color='dodgerblue', range= (range_min, range_max))

        ax.set_ylabel("[frequency]")
        plt.title("title")
        plt.legend(['data points'], loc='lower right')
        plt.show()
        plot_filename = '2D_plot.png'
        plt.savefig(os.path.join(plot_dir, plot_filename))

    elif heat is True:

        x = plot_data[x_handle]
        y = plot_data[y_handle]

        if full_data is True:
            bin_num_x = round((abs(min(x) + abs(max(x))) / width_x))
            bin_num_y = round((abs(min(y) + abs(max(y))) / width_y))
            range_min_y = min(y)
            range_max_y = max(y)
            range_min_x = min(x)
            range_max_x = max(x)

        elif stand_dev is True:
            mean_y = statistics.mean(y)
            stdev_y = statistics.stdev(y)
            threshold_y = sigma * stdev_y
            range_min_y = mean_y - threshold_y
            range_max_y = mean_y + threshold_y
            mean_x = statistics.mean(x)
            stdev_x = statistics.stdev(x)
            threshold_x = sigma * stdev_x
            range_min_x = mean_x - threshold_x
            range_max_x = mean_x + threshold_x
            bin_num_x = round((abs(range_max_x) + abs(range_min_x))/ width_x)
            bin_num_y = round((abs(range_max_y) + abs(range_min_y))/ width_y)

        elif over_ride is True:
            bin_num_x = round((abs(minimum) + abs(maximum)) / width_x)
            range_min_x = minimum_x
            range_max_x = maximum_x
            range_max_y = maximum_y
            range_min_y = minimum_y

        h = ax.hist2d(x, y, bins=(bin_num_x, bin_num_y), range=([range_min_x,range_max_x],[range_min_y,range_max_y]),cmap=hypatia_colormap)
        ax.set_xlabel(f'[{xaxis1}/{xaxis2}]')
        ax.set_ylabel(f'[{yaxis1}/{yaxis2}]')
        ax.set_title('Heatmap')
        plt.colorbar(h[3], label='Frequency')
        plt.show()

    elif both is True:
        x = plot_data[x_handle]
        y = plot_data[y_handle]

        if  full_data is True:
            range_min_x = min(x)
            range_max_x = max(x)
            range_min_y = min(y)
            range_max_y = max(y)
            bin_num_x = round((abs(range_max_x) + abs(range_min_x)) / width_x)
            bin_num_y = round((abs(range_max_y) + abs(range_min_y)) / width_y)

        elif stand_dev is True:
            mean_y = statistics.mean(y)
            stdev_y = statistics.stdev(y)
            threshold_y = sigma * stdev_y
            range_min_y = mean_y - threshold_y
            range_max_y = mean_y + threshold_y
            mean_x = statistics.mean(x)
            stdev_x = statistics.stdev(x)
            threshold_x = sigma * stdev_x
            range_min_x = mean_x - threshold_x
            range_max_x = mean_x + threshold_x
            bin_num_x = round((abs(range_max_x) + abs(range_min_x)) / width_x)
            bin_num_y = round((abs(range_max_y) + abs(range_min_y)) / width_y)

        elif over_ride is True:
            bin_num_x = round((abs(minimum) + abs(maximum)) / width_x)
            range_min_x = minimum_x
            range_max_x = maximum_x
            range_max_y = maximum_y
            range_min_y = minimum_y

        plt.close('all')
        fig = plt.figure(figsize=(8, 8))
        gs = fig.add_gridspec(2, 2, width_ratios=(7, 2), height_ratios=(2, 7), left=0.1, right=0.9, bottom=0.1, top=0.9, wspace=0.05, hspace=0.05)
        ax = fig.add_subplot(gs[1, 0])
        ax_histx = fig.add_subplot(gs[0, 0], sharex=ax)
        ax_histy = fig.add_subplot(gs[1, 1], sharey=ax)
        # Main heatmap
        h = ax.hist2d(x, y, bins=(bin_num_x, bin_num_y), range=([range_min_x, range_max_x], [range_min_y, range_max_y]), cmap=hypatia_colormap)
        ax.set_xlabel(f'[{xaxis1}/{xaxis2}]')
        ax.set_ylabel(f'[{yaxis1}/{yaxis2}]')
        # Marginal histograms
        ax_histx.hist(x, bins=bin_num_x, range=(range_min_x, range_max_x), color='#4e11b7', edgecolor='black')
        ax_histy.hist(y, bins=bin_num_y, range=(range_min_y, range_max_y), orientation='horizontal', color='#4e11b7', edgecolor='black')

        plt.setp(ax_histx.get_xticklabels(), visible=False)
        plt.setp(ax_histy.get_yticklabels(), visible=False)
        cbar = fig.colorbar(h[3], ax=ax_histy, orientation='vertical', fraction=0.15)
        cbar.set_label('amt of stars')
        plt.show()