import os
import statistics
import sys
from collections import Counter
import numpy as np
import math
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from hypatia.configs.file_paths import plot_dir
from hypatia.tools.web_query import get_graph_data

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

hypatia_colormap = colors

xaxis1 = 'Ca'
xaxis2 = 'H'
yaxis1 = 'C'
yaxis2 = 'H'

plot_data = get_graph_data(xaxis1=xaxis1, xaxis2=xaxis2, yaxis1=yaxis1, yaxis2=yaxis2)

if plot_data is not None:
    fig = go.Figure().set_subplots()
    x_handle = f'{xaxis1}'
    if xaxis2 is not None and xaxis2.lower()!= 'h':
        x_handle += f'_{xaxis2}'
    y_handle = f'{yaxis1}'
    if yaxis2 is not None and yaxis2.lower()!= 'h':
        y_handle += f'_{yaxis2}'

    hist = False
    heat = False
    both = True

    full_data = False
    stand_dev = True
    sigma = 3
    per_max = False
    percent = 30
    over_ride = False
    maximum = 0.85
    minimum = -0.45
    data = plot_data[x_handle]

    # specifically for heat
    width_x = 0.08
    width_y = 0.08
    minimum_y = 0.8
    minimum_x = 0.8
    maximum_y = 0.95
    maximum_x = 0.95

    if hist is True:
        if data is plot_data[x_handle]:
            fig = go.Figure(layout=go.Layout(
                xaxis=dict(
                    title=f'[{xaxis1}/{xaxis2}]'
                )
            ))
            width = 2 * math.log(10) * math.sqrt((element_err[xaxis1] ** 2) + (element_err[xaxis2] ** 2))
        else:
            fig = go.Figure(layout=go.Layout(
                xaxis=dict(
                    title=f'[{yaxis1}/{yaxis2}]'
                )
            ))
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

        # Create histogram using Plotly
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=data,
            xbins=dict(start=range_min, end=range_max, size=(range_max - range_min) / bins),
            marker=dict(color = '#4e11b7', line=dict(color='black', width=1)),
            name='data points'
        ))

        # Set layout
        fig.update_layout(
            title="title",
            xaxis_title='',
            yaxis_title='[frequency]',
            legend=dict(x=1, y=0, xanchor='right', yanchor='bottom'),
            bargap=0.1
        )

        # Show the plot
        fig.show()

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

        fig = go.Figure(data=go.Histogram2d(
            x=x,
            y=y,
            xbins=dict(start=range_min_x, end=range_max_x, size=(range_max_x - range_min_x) / bin_num_x),
            ybins=dict(start=range_min_y, end=range_max_y, size=(range_max_y - range_min_y) / bin_num_y),
            colorscale=hypatia_colormap,
            colorbar=dict(title='Frequency')
        ))

        # Update layout
        fig.update_layout(
            title='Heatmap',
            xaxis_title=f'[{xaxis1}/{xaxis2}]',
            yaxis_title=f'[{yaxis1}/{yaxis2}]'
        )

        # Show plot
        fig.show()

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

        # Create the subplot layout: 2 rows, 2 cols
        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.8, 0.2],
            row_heights=[0.2, 0.8],
            shared_xaxes=True,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            vertical_spacing=0.02,
            specs=[[{"type": "histogram"}, None],
                   [{"type": "histogram2d"}, {"type": "histogram"}]]
        )

        # Top histogram (x-axis)
        fig.add_trace(
            go.Histogram(
                x=x,
                xbins=dict(
                    start=range_min_x,
                    end=range_max_x,
                    size=(range_max_x - range_min_x) / bin_num_x
                ),
                marker=dict(color='#4e11b7', line=dict(color='black', width=1)),
                showlegend=False
            ),
            row=1, col=1
        )

        # Right histogram (y-axis, plotted horizontally)
        fig.add_trace(
            go.Histogram(
                y=y,
                ybins=dict(
                    start=range_min_y,
                    end=range_max_y,
                    size=(range_max_y - range_min_y) / bin_num_y
                ),
                marker=dict(color='#4e11b7', line=dict(color='black', width=1)),
                showlegend=False
            ),
            row=2, col=2
        )

        # Main 2D heatmap
        fig.add_trace(
            go.Histogram2d(
                x=x,
                y=y,
                xbins=dict(
                    start=range_min_x,
                    end=range_max_x,
                    size=(range_max_x - range_min_x) / bin_num_x
                ),
                ybins=dict(
                    start=range_min_y,
                    end=range_max_y,
                    size=(range_max_y - range_min_y) / bin_num_y
                ),
                colorscale=hypatia_colormap,
                colorbar=dict(title='Frequency'),
                showscale=True
            ),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            title="Heatmap with Marginal Histograms",
            xaxis2_title=f"[{xaxis1}/{xaxis2}]",
            yaxis2_title=f"[{yaxis1}/{yaxis2}]",
            bargap=0.05,
            showlegend=False
        )

        fig.show()

