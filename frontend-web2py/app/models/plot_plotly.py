import os
import sys
import math
from warnings import warn

import numpy as np

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


max_bins = 200
bin_tags = ['std dev', 'error']
color_pallets = ['hypatia', 'tritanomaly', 'monochrome', 'plasma', 'magma']
bin_tags_checker = {tag.strip().lower().replace(' ', ''): tag for tag in bin_tags}


def check_bin_size(bin_size: float, range_size: float) -> float:
    if range_size == 0:
        return 0.01
    if bin_size > range_size:
        return range_size
    min_bin_size = range_size / float(max_bins)
    return max(bin_size, min_bin_size)


def bin_argument(bin_size: str) -> str:
    if isinstance(bin_size, str):
        formatted_bin_size = bin_size.lower().strip().replace(' ', '')
        if formatted_bin_size in bin_tags_checker.keys():
            return bin_tags_checker[formatted_bin_size]
    # for all other case return the first  bin tag
    return bin_tags[0]


def calc_std(x_data: list[float | int]) -> float:
    """
    Calculate the error of a dataset.
    The error is defined as the standard deviation of the dataset.
    """
    if not x_data:
        return 0.0
    n = len(x_data)
    if n < 2:
        return 0.0
    mean = sum(x_data) / n
    variance = sum((x - mean) ** 2 for x in x_data) / (n - 1)
    return variance ** 0.5


def get_error(label: str) -> float | None:
    possible_element = label.lower().strip().replace('[', '').replace(']', '').replace(' ', '').replace('_', '')
    if '/' in possible_element:
        possible_element, possible_h = possible_element.split('/', 1)
        if possible_h == 'h':
            return representative_error[possible_element]
    return None


def get_bin_size(hist_bin_size, one_axis: np.array, one_range: float, label: str) -> float:
    try:
        hist_bin_size = float(hist_bin_size)
    except (ValueError, TypeError):
        hist_bin_size = bin_argument(hist_bin_size)
        if hist_bin_size == 'error':
            # can be None if no error is defined for the label
            hist_bin_size = get_error(label)
        if hist_bin_size is None or isinstance(hist_bin_size, str):
            # This sets the default bin size to the standard deviation of the data
            hist_bin_size = np.std(one_axis)
    hist_bin_size = check_bin_size(hist_bin_size, one_range)
    return hist_bin_size


def create_plotly_scatter(name: list[str],
                          xaxis: list[str | float | int], yaxis: list[str | float | int],
                          x_label: str = None, y_label: str = None,
                          star_count: int = None, planet_count: int = None,
                          do_xlog: bool = False, do_ylog: bool = False,
                          xaxisinv: bool = False, yaxisinv: bool = False,
                          do_gridlines: bool = False,
                          show_xyhist: bool = True,
                          xhist_bin_size: float | str = bin_tags[0], yhist_bin_size: float | str = bin_tags[0],
                          color_pallet: str = 'hypatia',
                          ) -> str:
    xaxis = np.array(xaxis)
    yaxis = np.array(yaxis)
    # Create a scatter plot
    min_x = np.min(xaxis)
    min_y = np.min(yaxis)
    max_x = np.max(xaxis)
    max_y = np.max(yaxis)
    range_x = max_x - min_x
    range_y = max_y - min_y
    xhist_bin_size = get_bin_size(hist_bin_size=xhist_bin_size, one_axis=xaxis, one_range=range_x, label=x_label)
    yhist_bin_size = get_bin_size(hist_bin_size=yhist_bin_size, one_axis=yaxis, one_range=range_y, label=y_label)
    test_label = f"Scatter Plot Test Label = Show Hist: {show_xyhist}, X-Bin: {xhist_bin_size}, Y-Bin: {yhist_bin_size}, Pallet: {color_pallet},"
    warn(test_label)

    fig = px.scatter(x=xaxis, y=yaxis)
    # Convert the figure to HTML
    return fig.to_html(include_plotlyjs=False)

# TO DO: transpile create_hypatia_plot() into the function create_plotly_scatter() (above_

def create_plotly_hist(name: list[str],
                          xaxis: list[str | float | int], yaxis: list[str | float | int],
                          x_label: str = None, y_label: str = None,
                          star_count: int = None, planet_count: int = None,
                          do_xlog: bool = False, do_ylog: bool = False,
                          xaxisinv: bool = False, yaxisinv: bool = False,
                          do_gridlines: bool = False,
                          show_xyhist: bool = True,
                          xhist_bin_size: float | str = bin_tags[0], yhist_bin_size: float | str = bin_tags[0],
                          color_pallet: str = 'hypatia'
                          ) -> str:
# just trying to get the heatmap to appear. This is a simpler version using px.
    xaxis = np.array(xaxis)
    yaxis = np.array(yaxis)
    hypatia = [
        [0.0, '#4e11b7'],
        [0.2, '#6c5ce7'],
        [0.4, '#dfe6e9'],
        [0.6, '#81ecec'],
        [0.8, '#92F7B0'],
        [0.9, '#F7C492'],
        [1.0, '#d63031']
    ]
#heatmap with marginal histograms
    fig = px.density_heatmap(
        x=xaxis,
        y=yaxis,
        nbinsx=xhist_bin_size,
        nbinsy=yhist_bin_size,
        marginal_x="histogram",
        marginal_y="histogram",
        color_continuous_scale=hypatia,
        labels={"x":x_label, "y":y_label}
    )
#formatting
    fig.update_layout(
        width=700,
        height=700,
        coloraxis_colorbar=dict(title="Frequency"),
        plot_bgcolor='white',
        bargap=0.05,
        showlegend=False
    )
    return fig.to_html(include_plotlyjs=True)


#would go where the previous code is under the function. More complex and uses go
    # xaxis = np.array(xaxis)
    # yaxis = np.array(yaxis)
    #
    # min_x, max_x = np.min(xaxis), np.max(xaxis)
    # min_y, max_y = np.min(yaxis), np.max(yaxis)
    # range_x, range_y = max_x - min_x, max_y - min_y
    #
    # xhist_bin_size = get_bin_size(hist_bin_size=xhist_bin_size, one_axis=xaxis, one_range=range_x, label=x_label)
    # yhist_bin_size = get_bin_size(hist_bin_size=yhist_bin_size, one_axis=yaxis, one_range=range_y, label=y_label)
    #
    # test_label = f"Histogram Plot Test Label = Show Hist: {show_xyhist}, X-Bin: {xhist_bin_size}, Y-Bin: {yhist_bin_size}, Pallet: {color_pallet}"
    # warn(test_label)
    #
    #
    # heatmap = go.Histogram2d(
    #     x=xaxis, y=yaxis,
    #     colorscale=hypatia,
    #     nbinsx = int(range_x / xhist_bin_size) if xhist_bin_size > 0 else 20,
    #     nbinsy = int(range_y / yhist_bin_size) if yhist_bin_size > 0 else 20,
    #     colorbar=dict(title="Frequency")
    # )
    #
    #
    # #subplots for main heatmap+hist

    # fig = make_subplots(
    #     rows=2, cols=2,
    #     column_widths=[0.8, 0.2],
    #     row_heights=[0.2, 0.8],
    #     shared_xaxes=True,
    #     shared_yaxes=True,
    #     horizontal_spacing=0.02,
    #     vertical_spacing=0.02,
    #     specs = [[{"type": "xy"}, None],
    #              [{"type": "xy"}, {"type": "xy"}]]
    # )

    # #top hist (x)

    # fig.add_trace(
    #     go.Histogram(
    #         x=xaxis,
    #         nbinsx=int(range_x / xhist_bin_size) if xhist_bin_size > 0 else 20,
    #         marker_color = "#4e11b7",
    #         showlegend = False
    #     ),
    # rows=1, cols=1
    # )
    #
    # # side hist (y)

    # fig.add_trace(
    #     go.Histogram(
    #         y=yaxis,
    #         nbinsy=int(range_y / yhist_bin_size) if yhist_bin_size > 0 else 20,
    #         marker_color="#4e11b7",
    #         showlegend=False
    #     ),
    #     rows=2, cols=2
    # )
    #
    # #formatting
    # fig.add_trace(heatmap, row=2, col=1)
    # fig.update_layout(
    #     title=f"{x_label} vs {y_label}",
    #     bargap=0.05,
    #     xaxis_title=x_label,
    #     yaxis_title=y_label,
    #     plot_bgcolor='white',
    #     width=700,
    #     height=700
    # )
    # else:
    #     #only heat

    #     fig = go.Figure(heatmap)
    #     fig.update_layout(
    #         title=f"{x_label} vs {y_label}",
    #         xaxis_title=x_label,
    #         yaxis_title=y_label,
    #         plot_bgcolor = 'white',
    #         width = 700,
    #         height = 700
    #     )
    # return fig.to_html(include_plotlyjs=True)


#OLD first function I made, does not even run the localhost, but I wanted to keep it so I can look back to it

# def create_hypatia_plot(xaxis1="N", xaxis2="H", yaxis1="Na", yaxis2="N",
#                         mode="both", width_override=None) -> str:
#     from hypatia.tools.web_query import get_graph_data
#     from hypatia.configs.file_paths import plot_dir
#     sys.path.append(os.path.dirname(__file__))
#
#     colors = [
#         [0.0, '#4e11b7'],
#         [0.2, '#6c5ce7'],
#         [0.4, '#dfe6e9'],
#         [0.6, '#81ecec'],
#         [0.8, '#92F7B0'],
#         [0.9, '#F7C492'],
#         [1.0, '#d63031']
#     ]
#
#     element_err = {
#         "Ag": 0.4,
#         "Al": 0.12,
#         "Al_II": 0.3,
#         "Au": 0.6,
#         "Ba": 0.3,
#         "Ba_II": 0.38,
#         "Be": 0.24,
#         "Be_II": 0.1,
#         "C": 0.18,
#         "Ca": 0.12,
#         "Ca_II": 0.06,
#         "Cd": 0.5,
#         "Ce": 0.152,
#         "Ce_II": 0.14,
#         "Cl": 0.46,
#         "Co": 0.08,
#         "Co_II": 0.1,
#         "Cr": 0.09,
#         "Cr_II": 0.132,
#         "Cu": 0.16,
#         "Cu_II": 0.46,
#         "Dy": 0.8,
#         "Dy_II": 0.22,
#         "Er": 0.4,
#         "Er_II": 0.32,
#         "Eu": 0.22,
#         "Eu_II": 0.2,
#         "F": 0.24,
#         "Fe": 0.08,
#         "Ga": 0.4,
#         "Ga_II": 0.38,
#         "Gd": 1.2,
#         "Gd_II": 0.26,
#         "Hf": 0.4,
#         "Hf_II": 0.36,
#         "Hg_II": 0.36,
#         "Ho_II": 0.42,
#         "In_II": 0.4,
#         "Ir": 0.56,
#         "K": 0.08,
#         "La": 0.172,
#         "La_II": 0.44,
#         "Li": 0.2,
#         "Lu_II": 0.3,
#         "Mg": 0.14,
#         "Mn": 0.112,
#         "Mn_II": 0.112,
#         "Mo": 0.24,
#         "Mo_II": 0.4,
#         "N": 0.22,
#         "Na": 0.08,
#         "Nb": 0.52,
#         "Nb_II": 0.3,
#         "Nd": 0.14,
#         "Nd_II": 0.14,
#         "Ni": 0.1,
#         "Ni_II": 0.16,
#         "O": 0.18,
#         "Os": 0.22,
#         "P": 0.08,
#         "Pb": 0.44,
#         "Pb_II": 0.44,
#         "Pd": 0.38,
#         "Pr": 0.26,
#         "Pr_II": 0.2,
#         "Pt": 0.3,
#         "Rb": 0.24,
#         "Re_II": 0.3,
#         "Rh": 0.44,
#         "Ru": 0.24,
#         "Ru_II": 0.34,
#         "S": 0.18,
#         "Sb": 0.34,
#         "Sc": 0.1,
#         "Sc_II": 0.18,
#         "Se": 0.5,
#         "Si": 0.1,
#         "Si_II": 0.1,
#         "Sm": 0.14,
#         "Sm_II": 0.31,
#         "Sn": 0.44,
#         "Sr": 0.212,
#         "Sr_II": 0.3,
#         "Tb_II": 0.22,
#         "Tc": 0.2,
#         "Te": 0.54,
#         "Th": 0.08,
#         "Th_II": 0.28,
#         "Ti": 0.1,
#         "Ti_II": 0.12,
#         "Tm_II": 0.4,
#         "V": 0.14,
#         "V_II": 0.21,
#         "W": 0.68,
#         "W_II": 0.2,
#         "Y": 0.17,
#         "Y_II": 0.16,
#         "Yb_II": 0.28,
#         "Zn": 0.152,
#         "Zn_II": 0.62,
#         "Zr": 0.2,
#         "Zr_II": 0.16
#     }
#
#     hypatia_colormap = colors
#
#     # same setup logic you already have:
#     if xaxis1 == "H":
#         width_x = element_err[xaxis2]
#     elif xaxis2 == "H":
#         width_x = element_err[xaxis1]
#     else:
#         width_x = math.sqrt((element_err[xaxis1])**2 + (element_err[xaxis2])**2)
#
#     if yaxis1 == "H":
#         width_y = element_err[yaxis2]
#     elif yaxis2 == "H":
#         width_y = element_err[yaxis1]
#     else:
#         width_y = math.sqrt((element_err[yaxis1])**2 + (element_err[yaxis2])**2)
#
#     plot_data = get_graph_data(xaxis1=xaxis1, xaxis2=xaxis2, yaxis1=yaxis1, yaxis2=yaxis2)
#     if plot_data is None:
#         return "<p>No data available.</p>"
#
#     x_handle = f"{xaxis1}_{xaxis2}"
#     y_handle = f"{yaxis1}_{yaxis2}"
#     x = plot_data[x_handle]
#     y = plot_data[y_handle]
#
#     # Choose plot mode
#     if mode == "hist":
#         fig = go.Figure(go.Histogram(x=x, marker_color="#4e11b7"))
#         fig.update_layout(title="Histogram", xaxis_title=f"[{xaxis1}/{xaxis2}]", yaxis_title="Frequency")
#
#     elif mode == "heat":
#         fig = go.Figure(go.Histogram2d(x=x, y=y, colorscale=hypatia_colormap))
#         fig.update_layout(title="Heatmap", xaxis_title=f"[{xaxis1}/{xaxis2}]", yaxis_title=f"[{yaxis1}/{yaxis2}]")
#
#     else:  # both
#         fig = make_subplots(
#             rows=2, cols=2,
#             column_widths=[0.8, 0.2],
#             row_heights=[0.2, 0.8],
#             shared_xaxes=True,
#             shared_yaxes=True,
#             specs=[[{"type": "histogram"}, None],
#                    [{"type": "histogram2d"}, {"type": "histogram"}]]
#         )
#         fig.add_trace(go.Histogram(x=x, marker_color="#4e11b7"), row=1, col=1)
#         fig.add_trace(go.Histogram(y=y, marker_color="#4e11b7"), row=2, col=2)
#         fig.add_trace(go.Histogram2d(x=x, y=y, colorscale=hypatia_colormap), row=2, col=1)
#         fig.update_layout(title="Heatmap with Marginal Histograms")
#
#     # Convert figure to HTML
#     html_str = fig.to_html(include_plotlyjs="cdn", full_html=True)
#     return html_str





