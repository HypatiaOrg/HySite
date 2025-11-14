import os
import sys
import math
from warnings import warn

import numpy as np

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


default_color_pallet = 'hypatia'

color_pallets = {
    'hypatia': [
        [0.0, '#4e11b7'],
        [0.2, '#6c5ce7'],
        [0.4, '#dfe6e9'],
        [0.6, '#81ecec'],
        [0.8, '#92F7B0'],
        [0.9, '#F7C492'],
        [1.0, '#d63031']
    ],
}


max_bins = 200
bin_tags = ['std dev', 'error']
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


def get_bin_number(hist_bin_size, one_axis: np.array, one_range: float, label: str) -> int:
    try:
        hist_bin_size = float(hist_bin_size)
    except (ValueError, TypeError):
        hist_bin_size = bin_argument(hist_bin_size)
        if hist_bin_size == 'error':
            # can be None if no error is defined for the label
            hist_bin_size = get_error(label)
        else:
            #  hist_bin_size is None or isinstance(hist_bin_size, str):
            # This sets the default bin size to the standard deviation of the data
            hist_bin_size = np.std(one_axis)
    hist_bin_size = check_bin_size(hist_bin_size, one_range)
    n_bins = max(int(np.round(one_range / hist_bin_size)), 1)
    return n_bins


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
    xaxis = np.array(xaxis)
    yaxis = np.array(yaxis)
    # Create a scatter plot
    min_x = np.min(xaxis)
    min_y = np.min(yaxis)
    max_x = np.max(xaxis)
    max_y = np.max(yaxis)
    range_x = max_x - min_x
    range_y = max_y - min_y
    nbinsx = get_bin_number(hist_bin_size=xhist_bin_size, one_axis=xaxis, one_range=range_x, label=x_label)
    nbinsy = get_bin_number(hist_bin_size=yhist_bin_size, one_axis=yaxis, one_range=range_y, label=y_label)
    test_label = f'Scatter Plot Test Label = Show Hist: {show_xyhist}, X-Bin: {xhist_bin_size}, Y-Bin: {yhist_bin_size}, Pallet: {color_pallet},'
    color_continuous_scale = color_pallets.get(color_pallet, default_color_pallet)
    warn(test_label)

    # heatmap with marginal histograms
    fig = px.density_heatmap(
        x=xaxis,
        y=yaxis,
        nbinsx=nbinsx,
        nbinsy=nbinsy,
        marginal_x='histogram',
        marginal_y='histogram',
        color_continuous_scale=color_continuous_scale,
        labels={'x': x_label, 'y': y_label}
    )
    # formatting
    fig.update_layout(
        width=700,
        height=700,
        coloraxis_colorbar=dict(title='Frequency'),
        plot_bgcolor='white',
        bargap=0.05,
        showlegend=False
    )
    return fig.to_html(include_plotlyjs=True)
