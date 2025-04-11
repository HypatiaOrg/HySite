import os
import statistics
from matplotlib.colors import LinearSegmentedColormap
import sys
from collections import Counter

import matplotlib as mpl
from django.template.defaulttags import widthratio
import numpy as np

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
    '#4e11b7',  # xkcd purple/blue
    '#6c5ce7',  # vibrant indigo
    '#dfe6e9',  # neutral white-silver
    '#81ecec',  # aqua
    '#55efc4',  # mint green
    '#ff7675',  # coral
    '#d63031',  # strong red

]

hypatia_colormap = LinearSegmentedColormap.from_list("hypatia_colormap", colors)

xaxis1 = 'Cu'
xaxis2 = 'Fe'
yaxis1 = 'S'
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
    hist = False
    heat = False
    both = True

    width = 0.08
    full_data = False
    stand_dev = True
    sigma = 3
    per_max = False
    percent = 30
    over_ride = False
    maximum = 0.85
    minimum = -0.45
    data = plot_data[y_handle]
    #specifically for heat
    minimum_y = 0.8
    minimum_x = 0.8
    maximum_y = 0.95
    maximum_x = 0.95


    if hist is True:
        if full_data is True:
            bins = round((abs(min(plot_data[y_handle]) + abs(max(plot_data[y_handle]))) / width))
            range_min = (min(plot_data[y_handle]))
            range_max = (max(plot_data[y_handle]))

        elif stand_dev is True:
            mean = statistics.mean(plot_data[y_handle])
            stdev = statistics.stdev(plot_data[y_handle])
            threshold = sigma*stdev
            range_min = mean-threshold
            range_max = mean+threshold
            bins = round((abs(range_min)+abs(range_max))/width)

        elif per_max is True:
            bins_init = round((abs(min(plot_data[y_handle]))/width))
            hist = np.histogram(plot_data[y_handle], bins=bins_init)
            norm_hist = hist[0]/max(hist[0])
            bin_edges_init = hist[1]
            threshold = percent*0.01
            keep_bin_indices = np.where(norm_hist >= threshold)[0] #identify the indices to keep
            bin_edges = bin_edges_init[keep_bin_indices]
            bin_edges_upper = bin_edges_init[keep_bin_indices + 1]
            filtered_data = []
            for lower, upper in zip(bin_edges, bin_edges_upper):
                filtered_data.extend([x for x in plot_data[y_handle] if lower <= x < upper])
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
        ax.set_xlabel(f'[{yaxis1}/{yaxis2}]')
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
            bin_num_x = round((abs(min(x) + abs(max(x))) / width))
            bin_num_y = round((abs(min(y) + abs(max(y))) / width))
            range_min_y = min(y)
            range_max_y = max(y)
            range_min_x = min(x)
            range_max_x = max(x)

        elif stand_dev is True:
            mean_y = statistics.mean(plot_data[y_handle])
            stdev_y = statistics.stdev(plot_data[y_handle])
            threshold_y = sigma * stdev_y
            range_min_y = mean_y - threshold_y
            range_max_y = mean_y + threshold_y
            mean_x = statistics.mean(plot_data[x_handle])
            stdev_x = statistics.stdev(plot_data[x_handle])
            threshold_x = sigma * stdev_x
            range_min_x = mean_x - threshold_x
            range_max_x = mean_x + threshold_x
            bin_num_x = round((abs(range_max_x) + abs(range_min_x))/ width)
            bin_num_y = round((abs(range_max_y) + abs(range_min_y))/ width)

        elif per_max is True:
            bin_x = round((abs(min(x) + abs(max(x))) / width))
            hist_x = np.histogram(plot_data[x_handle], bins=bin_x)
            norm_hist_x = hist_x[0]/np.max(hist_x[0])
            bin_y = round((abs(min(y)) + abs(max(y)) / width))
            hist_y = np.histogram(plot_data[y_handle], bins=bin_y)
            norm_hist_y = hist_y[0]/np.max(hist_y[0])
            bin_x_init = hist_x[1]
            bin_y_init = hist_y[1]
            threshold = percent*0.01

            keep_bin_indices_x = np.where(norm_hist_x >= threshold)[0]
            bin_edges_x = bin_x_init[keep_bin_indices_x]
            bin_edges_upper_x = bin_x_init[keep_bin_indices_x + 1]
            filtered_data_x = []
            for lower, upper in zip(bin_edges_x, bin_edges_upper_x):
                filtered_data_x.extend([i for i in x if lower <= i < upper])
            filtered_data_x = np.array(filtered_data_x)
            x = np.array(filtered_data_x)
            range_min_x = filtered_data_x.min()
            range_max_x = filtered_data_x.max()
            bin_num_x = round((abs(range_min_x) + abs(range_max_x)) / width)

            keep_bin_indices_y = np.where(norm_hist_y >= threshold)[0]
            bin_edges_y = bin_y_init[keep_bin_indices_y]
            bin_edges_upper_y = bin_y_init[keep_bin_indices_y + 1]
            filtered_data_y = []
            for lower, upper in zip(bin_edges_y, bin_edges_upper_y):
                filtered_data_y.extend([i for i in y if lower <= i < upper])
            filtered_data_y = np.array(filtered_data_y)
            y = np.array(filtered_data_y)
            range_min_y = filtered_data_y.min()
            range_max_y = filtered_data_y.max()
            bin_num_y = round((abs(range_min_y) + abs(range_max_y)) / width)
        elif over_ride is True:
            bin_num_x = round((abs(minimum) + abs(maximum)) / width)
            range_min_x = minimum_x
            range_max_x = maximum_x
            range_max_y = maximum_y
            range_min_y = minimum_y

        h = ax.hist2d(x, y, bins=(bin_num_x, bin_num_y), range=([range_min_x,range_max_x],[range_min_y,range_max_y]),cmap='Spectral')
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
            bin_num_x = round((abs(range_max_x) + abs(range_min_x)) / width)
            bin_num_y = round((abs(range_max_y) + abs(range_min_y)) / width)

        elif stand_dev is True:
            mean_y = statistics.mean(plot_data[y_handle])
            stdev_y = statistics.stdev(plot_data[y_handle])
            threshold_y = sigma * stdev_y
            range_min_y = mean_y - threshold_y
            range_max_y = mean_y + threshold_y
            mean_x = statistics.mean(plot_data[x_handle])
            stdev_x = statistics.stdev(plot_data[x_handle])
            threshold_x = sigma * stdev_x
            range_min_x = mean_x - threshold_x
            range_max_x = mean_x + threshold_x
            bin_num_x = round((abs(range_max_x) + abs(range_min_x)) / width)
            bin_num_y = round((abs(range_max_y) + abs(range_min_y)) / width)

        elif per_max is True:
            bin_x = round((abs(min(x) + abs(max(x))) / width))
            hist_x = np.histogram(plot_data[x_handle], bins=bin_x)
            norm_hist_x = hist_x[0] / np.max(hist_x[0])
            bin_y = round((abs(min(y) + abs(max(y))) / width))
            hist_y = np.histogram(plot_data[y_handle], bins=bin_y)
            norm_hist_y = hist_y[0] / np.max(hist_y[0])
            bin_x_init = hist_x[1]
            bin_y_init = hist_y[1]
            threshold = percent * 0.01

            keep_bin_indices_x = np.where(norm_hist_x >= threshold)[0]
            bin_edges_x = bin_x_init[keep_bin_indices_x]
            bin_edges_upper_x = bin_x_init[keep_bin_indices_x + 1]
            filtered_data_x = []
            for lower, upper in zip(bin_edges_x, bin_edges_upper_x):
                filtered_data_x.extend([i for i in x if lower <= i < upper])
            filtered_data_x = np.array(filtered_data_x)
            x = np.array(filtered_data_x)
            range_min_x = filtered_data_x.min()
            range_max_x = filtered_data_x.max()
            bin_num_x = round((abs(range_min_x) + abs(range_max_x)) / width)

            keep_bin_indices_y = np.where(norm_hist_y >= threshold)[0]
            bin_edges_y = bin_y_init[keep_bin_indices_y]
            bin_edges_upper_y = bin_y_init[keep_bin_indices_y + 1]
            filtered_data_y = []
            for lower, upper in zip(bin_edges_y, bin_edges_upper_y):
                filtered_data_y.extend([i for i in y if lower <= i < upper])
            filtered_data_y = np.array(filtered_data_y)
            y = np.array(filtered_data_y)
            range_min_y = filtered_data_y.min()
            range_max_y = filtered_data_y.max()
            bin_num_y = round((abs(range_min_y) + abs(range_max_y)) / width)

        elif over_ride is True:
            bin_num_x = round((abs(minimum) + abs(maximum)) / width)
            range_min_x = minimum_x
            range_max_x = maximum_x
            range_max_y = maximum_y
            range_min_y = minimum_y

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
        ax_histx.hist(x, bins=bin_num_x, range=(range_min_x, range_max_x), color='xkcd:purple/blue', edgecolor='black')
        ax_histy.hist(y, bins=bin_num_y, range=(range_min_y, range_max_y), orientation='horizontal', color='xkcd:purple/blue', edgecolor='black')

        plt.setp(ax_histx.get_xticklabels(), visible=False)
        plt.setp(ax_histy.get_yticklabels(), visible=False)
        cbar = fig.colorbar(h[3], ax=ax_histy, orientation='vertical', fraction=0.15)
        cbar.set_label('amt of stars')
        plt.show()