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
    "Ag": 0.4,
    "Al": 0.12,
    "Al_II": 0.3,
    "Au": 0.6,
    "Ba": 0.3,
    "Ba_II": 0.38,
    "Be": 0.24,
    "Be_II": 0.1,
    "C": 0.18,
    "Ca": 0.12,
    "Ca_II": 0.06,
    "Cd": 0.5,
    "Ce": 0.152,
    "Ce_II": 0.14,
    "Cl": 0.46,
    "Co": 0.08,
    "Co_II": 0.1,
    "Cr": 0.09,
    "Cr_II": 0.132,
    "Cu": 0.16,
    "Cu_II": 0.46,
    "Dy": 0.8,
    "Dy_II": 0.22,
    "Er": 0.4,
    "Er_II": 0.32,
    "Eu": 0.22,
    "Eu_II": 0.2,
    "F": 0.24,
    "Fe": 0.08,
    "Ga": 0.4,
    "Ga_II": 0.38,
    "Gd": 1.2,
    "Gd_II": 0.26,
    "Hf": 0.4,
    "Hf_II": 0.36,
    "Hg_II": 0.36,
    "Ho_II": 0.42,
    "In_II": 0.4,
    "Ir": 0.56,
    "K": 0.08,
    "La": 0.172,
    "La_II": 0.44,
    "Li": 0.2,
    "Lu_II": 0.3,
    "Mg": 0.14,
    "Mn": 0.112,
    "Mn_II": 0.112,
    "Mo": 0.24,
    "Mo_II": 0.4,
    "N": 0.22,
    "Na": 0.08,
    "Nb": 0.52,
    "Nb_II": 0.3,
    "Nd": 0.14,
    "Nd_II": 0.14,
    "Ni": 0.1,
    "Ni_II": 0.16,
    "O": 0.18,
    "Os": 0.22,
    "P": 0.08,
    "Pb": 0.44,
    "Pb_II": 0.44,
    "Pd": 0.38,
    "Pr": 0.26,
    "Pr_II": 0.2,
    "Pt": 0.3,
    "Rb": 0.24,
    "Re_II": 0.3,
    "Rh": 0.44,
    "Ru": 0.24,
    "Ru_II": 0.34,
    "S": 0.18,
    "Sb": 0.34,
    "Sc": 0.1,
    "Sc_II": 0.18,
    "Se": 0.5,
    "Si": 0.1,
    "Si_II": 0.1,
    "Sm": 0.14,
    "Sm_II": 0.31,
    "Sn": 0.44,
    "Sr": 0.212,
    "Sr_II": 0.3,
    "Tb_II": 0.22,
    "Tc": 0.2,
    "Te": 0.54,
    "Th": 0.08,
    "Th_II": 0.28,
    "Ti": 0.1,
    "Ti_II": 0.12,
    "Tm_II": 0.4,
    "V": 0.14,
    "V_II": 0.21,
    "W": 0.68,
    "W_II": 0.2,
    "Y": 0.17,
    "Y_II": 0.16,
    "Yb_II": 0.28,
    "Zn": 0.152,
    "Zn_II": 0.62,
    "Zr": 0.2,
    "Zr_II": 0.16
}

hypatia_colormap = colors

xaxis1 = 'N'
xaxis2 = 'H'
yaxis1 = 'Na'
yaxis2 = 'N'

if xaxis1 == "H":
    width_x = element_err[xaxis2]
elif xaxis2 == "H":
    width_x = element_err[xaxis1]
else:
    width_x = math.sqrt((element_err[xaxis1]) ** 2 + (element_err[xaxis2]) ** 2)

if yaxis1 == "H":
    width_y = element_err[yaxis2]
elif yaxis2 == "H":
    width_y = element_err[yaxis1]
else:
    width_y = math.sqrt((element_err[yaxis1]) ** 2 + (element_err[yaxis2]) ** 2)

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

    full_data = True
    stand_dev = False
    sigma = 4
    per_max = False
    percent = 30
    over_ride = False
    maximum = 0.85
    minimum = -0.45
    data = plot_data[x_handle]

    # specifically for heat

    minimum_y = 0.8
    minimum_x = 0.8
    maximum_y = 0.95
    maximum_x = 0.95

    if hist is True:
        if data is plot_data[x_handle]:

            width = width_x

            if full_data is True:
                bins = round((abs(min(data) + abs(max(data))) / width))
                range_min = (min(data))
                range_max = (max(data))

            elif stand_dev is True:
                mean = statistics.mean(data)
                stdev = statistics.stdev(data)
                threshold = sigma * stdev
                range_min = mean - threshold
                range_max = mean + threshold
                bins = round((abs(range_min) + abs(range_max)) / width)
            elif per_max is True:
                bins_init = round((abs(min(data)) / width))
                hist = np.histogram(data, bins=bins_init)
                norm_hist = hist[0] / max(hist[0])
                bin_edges_init = hist[1]
                threshold = percent * 0.01
                keep_bin_indices = np.where(norm_hist >= threshold)[0]  # identify the indices to keep
                bin_edges = bin_edges_init[keep_bin_indices]
                bin_edges_upper = bin_edges_init[keep_bin_indices + 1]
                filtered_data = []
                for lower, upper in zip(bin_edges, bin_edges_upper):
                    filtered_data.extend([x for x in data if lower <= x < upper])
                filtered_data = np.array(filtered_data)
                data = filtered_data
                range_min = filtered_data.min()
                range_max = filtered_data.max()
                bins = round((abs(range_min) + abs(range_max)) / width)

            elif over_ride is True:
                bins = round((abs(minimum) + abs(maximum)) / width)
                range_min = minimum
                range_max = maximum

            # Create histogram using Plotly
            fig = go.Figure()

            fig.add_trace(go.Histogram(
                x=data,
                xbins=dict(start=range_min, end=range_max, size=(range_max - range_min) / width),
                marker=dict(color='#4e11b7', line=dict(color='black', width=1)),
                name='data points'
            ))

            # Set layout
            fig.update_layout(
                title="Histogram",
                xaxis=dict(title=f'[{xaxis1}/{xaxis2}]'),
                yaxis_title='[frequency]',
                legend=dict(x=1, y=0, xanchor='right', yanchor='bottom'),
                bargap=0.1
            )

            # Show the plot
            fig.show()
        else:

            width = width_y

            if full_data is True:
                bins = round((abs(min(data) + abs(max(data))) / width))
                range_min = (min(data))
                range_max = (max(data))

            elif stand_dev is True:
                mean = statistics.mean(data)
                stdev = statistics.stdev(data)
                threshold = sigma * stdev
                range_min = mean - threshold
                range_max = mean + threshold
                bins = round((abs(range_min) + abs(range_max)) / width)
            elif per_max is True:
                bins_init = round((abs(min(data)) / width))
                hist = np.histogram(data, bins=bins_init)
                norm_hist = hist[0] / max(hist[0])
                bin_edges_init = hist[1]
                threshold = percent * 0.01
                keep_bin_indices = np.where(norm_hist >= threshold)[0]  # identify the indices to keep
                bin_edges = bin_edges_init[keep_bin_indices]
                bin_edges_upper = bin_edges_init[keep_bin_indices + 1]
                filtered_data = []
                for lower, upper in zip(bin_edges, bin_edges_upper):
                    filtered_data.extend([x for x in data if lower <= x < upper])
                filtered_data = np.array(filtered_data)
                data = filtered_data
                range_min = filtered_data.min()
                range_max = filtered_data.max()
                bins = round((abs(range_min) + abs(range_max)) / width)

            elif over_ride is True:
                bins = round((abs(minimum) + abs(maximum)) / width)
                range_min = minimum
                range_max = maximum

            # Create histogram using Plotly
            fig = go.Figure()

            fig.add_trace(go.Histogram(
                x=data,
                xbins=dict(start=range_min, end=range_max, size=(range_max - range_min) / width),
                marker=dict(color='#4e11b7', line=dict(color='black', width=1)),
                name='data points'
            ))

            # Set layout
            fig.update_layout(
                title="Histogram",
                xaxis=dict(title=f"[{yaxis1}/{yaxis2}]"),
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
            xbins=dict(start=range_min_x, end=range_max_x, size=(range_max_x - range_min_x) / width_x),
            ybins=dict(start=range_min_y, end=range_max_y, size=(range_max_y - range_min_y) / width_y),
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
                    size=width_x
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
                    size=width_y
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
                    size=width_x
                ),
                ybins=dict(
                    start=range_min_y,
                    end=range_max_y,
                    size=width_y
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
            showlegend=False,
            width=600,
            height=600
        )

        fig.show()

