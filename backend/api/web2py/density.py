"""
The data shaping behind the density page: a heat map of the scatter page's points, with histograms along
the axes. Decided here: the points with a value on both axes, each axis's plotted range and bin width (a
number the visitor typed, the parameter's representative error, or the standard deviation of the data),
the colour scale, and the axis decisions (a logarithmic axis needs positive values). The frontend only
draws what comes back.

Until October 2026 these rules lived in web2py's plot code (models/plot_plotly.py on the plotly branch);
they moved here with the same arithmetic, so the plot is the same bin for bin. Two cases that raised an
error there are decided here instead: the "error" bin size of an element ratio (the two representative
errors added in quadrature) and of a stellar or planet parameter (the hand-set table PARAMETER_ERRORS).
"""
import math

import numpy as np

from api.v2.data_process import representative_error
from api.web2py.data_process import is_true_str

# the colour scales a visitor can choose: Hypatia's own (HyPurple) as colour stops, the others by their Plotly names
COLOR_PALETTES = {
    'HyPurple': [[0.0, '#4e11b7'], [0.2, '#6c5ce7'], [0.4, '#dfe6e9'], [0.6, '#81ecec'],
                [0.8, '#92F7B0'], [0.9, '#F7C492'], [1.0, '#d63031']],
    'Viridis': 'Viridis',
    'Plasma': 'Plasma',
    'Cividis': 'Cividis',
    'Inferno': 'Inferno',
    'Turbo': 'Turbo',
}
DEFAULT_COLOR_PALETTE = 'HyPurple'
# the histograms take the first colour of the scale
HISTOGRAM_COLORS = {'Viridis': '#440154', 'Plasma': '#0d0887', 'Inferno': '#000004', 'Cividis': '#00224e',
                    'Turbo': '#30123b'}
DEFAULT_HISTOGRAM_COLOR = '#4e11b7'

# the keywords a bin size field accepts; the first is what an empty or unreadable field means
BIN_TAGS = ['std dev', 'error']
# the representative error of each stellar and planet parameter, the "error" bin size, in the parameter's units
# (the owner's table of 2026-11-02; elements and ratios come from the catalog summary instead)
PARAMETER_ERRORS = {
    'raj2000': 1.0, 'decj2000': 1.0, 'dist': 1.0, 'x_pos': 0.1, 'y_pos': 0.1, 'z_pos': 0.1,
    'teff': 150.0, 'logg': 0.1, 'sptype_num': 1.0, 'vmag': 0.1, 'bmag': 0.1, 'bv': 0.15,
    'pm_ra': 0.1, 'pm_dec': 0.1, 'u_vel': 1.0, 'v_vel': 1.0, 'w_vel': 1.0, 'disk_num': 1.0,
    'mass': 0.1, 'rad': 0.1,
    'pl_radius': 0.1, 'pl_mass': 0.05, 'period': 0.01, 'semi_major_axis': 0.05, 'eccentricity': 0.05,
    'inclination': 1.0,
}
# the menu choices that have no error of their own (the plot shows their ranked number, data_process.ranked_string_params)
# and what to tell a visitor who asks for "error" bins with one of them on the axis: the bins fall back to "std dev"
# and carry the text, which the frontend shows next to the bin size box (controllers/default.py, bin_warnings)
BIN_WARNINGS = {'sptype': 'Please plot Spectral Type Number', 'disk': 'Please plot Disk Number'}
MAX_BINS = 200
# how the plotted range is chosen: the whole data, the mean +- sigma standard deviations, or typed limits.
# The page offers only the first today; the others are ready for the controls to come.
RANGE_MODES = ['full data', 'std dev', 'manual']
DEFAULT_SIGMA = 4.0


def color_scale(color_palette: str | None) -> tuple[str, list | str, str]:
    """The palette's name, its colour scale and its histogram colour; an unknown choice gets the default."""
    name = color_palette if color_palette in COLOR_PALETTES else DEFAULT_COLOR_PALETTE
    scale = COLOR_PALETTES[name]
    if isinstance(scale, list):
        histogram_color = scale[0][1]
    else:
        histogram_color = HISTOGRAM_COLORS.get(scale, DEFAULT_HISTOGRAM_COLOR)
    return name, scale, histogram_color


def bin_request(bin_size: str | float | None) -> float | str:
    """What a bin size field asks for: the number typed, or one of BIN_TAGS (the first for anything else)."""
    try:
        return float(bin_size)
    except (ValueError, TypeError):
        pass
    key = str(bin_size or '').lower().strip().replace(' ', '')
    for tag in BIN_TAGS:
        if key == tag.replace(' ', ''):
            return tag
    return BIN_TAGS[0]


def sample_std(values: list[float]) -> float:
    """The sample standard deviation (n - 1 in the denominator), 0 for fewer than two values."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    return float(variance ** 0.5)


def parameter_error(value_type: str, param_id) -> float | None:
    """
    The representative error of a plotted parameter, the "error" bin size: an element's from the catalog
    summary, a ratio's from both elements added in quadrature, a stellar or planet parameter's from the
    hand-set table PARAMETER_ERRORS. None when nothing is known.
    """
    if value_type == 'element':
        return representative_error.get(str(param_id), None)
    if value_type == 'element_ratio':
        numerator = representative_error.get(str(param_id.numerator), None)
        denominator = representative_error.get(str(param_id.denominator), None)
        if numerator is None or denominator is None:
            return None
        return math.sqrt(numerator ** 2 + denominator ** 2)
    return PARAMETER_ERRORS.get(param_id, None)


def check_bin_size(bin_size: float, range_size: float) -> float:
    """A bin width that fits the range: no wider than the range, no narrower than MAX_BINS bins would make."""
    if range_size == 0:
        return 0.01
    if bin_size > range_size:
        return range_size
    return max(bin_size, range_size / float(MAX_BINS))


def axis_range(values: np.ndarray, range_mode: str = 'full data', sigma: float = DEFAULT_SIGMA,
               manual_min: float | None = None, manual_max: float | None = None) -> tuple[float, float]:
    """The plotted range of one axis, by RANGE_MODES; "full data" unless the mode's inputs are complete."""
    if range_mode == 'manual' and manual_min is not None and manual_max is not None:
        return float(manual_min), float(manual_max)
    if range_mode == 'std dev':
        mean = np.mean(values)
        stdev = np.std(values)
        return float(mean - sigma * stdev), float(mean + sigma * stdev)
    return float(np.min(values)), float(np.max(values))


def axis_bins(values: np.ndarray, requested: str | float | None, value_type: str, param_id,
              range_mode: str = 'full data', sigma: float = DEFAULT_SIGMA,
              manual_min: float | None = None, manual_max: float | None = None,
              selected: str | None = None) -> dict:
    """
    One axis's bins: the range (start, end), the bin width (size) and how it was chosen (mode: "number",
    "error" or "std dev"; "error" falls back to "std dev" when the parameter has no representative error).
    With "error" asked for a menu choice in BIN_WARNINGS (selected: the setting as the visitor chose it), the
    bins carry its warning text and use "std dev".
    """
    start, end = axis_range(values, range_mode=range_mode, sigma=sigma, manual_min=manual_min, manual_max=manual_max)
    request = bin_request(requested)
    warning = BIN_WARNINGS.get(selected, None) if request == 'error' else None
    width = None
    if isinstance(request, float):
        width, mode = request, 'number'
    elif request == 'error' and warning is None:
        width, mode = parameter_error(value_type, param_id), 'error'
    if width is None:
        width, mode = sample_std(list(values)), 'std dev'
    bins = {'start': start, 'end': end, 'size': check_bin_size(width, end - start), 'mode': mode}
    if warning:
        bins['warning'] = warning
    return bins


def valid_points(outputs: dict) -> tuple[list[str], np.ndarray, np.ndarray]:
    """The names and the x and y values of the points with a value on both axes."""
    names = outputs.get('name', [])
    xaxis = np.array([np.nan if value is None else value for value in outputs.get('xaxis', [])], dtype=float)
    yaxis = np.array([np.nan if value is None else value for value in outputs.get('yaxis', [])], dtype=float)
    valid = np.isfinite(xaxis) & np.isfinite(yaxis)
    return [name for name, is_valid in zip(names, valid) if is_valid], xaxis[valid], yaxis[valid]


def marginal_bins(xaxis: np.ndarray, yaxis: np.ndarray, axis_mapping: dict, settings) -> dict | None:
    """The bins of the histograms along the x and y axes (axis_bins for each), for the density page and for
    the scatter and targets pages' optional histograms; None without points."""
    if not len(xaxis):
        return None
    range_mode = settings.get('range_mode', 'full data')
    return {
        'xaxis': axis_bins(xaxis, settings.get('xhist_bin_size', None), *axis_mapping['x'], range_mode=range_mode,
                           selected=settings.get('xaxis1', None)),
        'yaxis': axis_bins(yaxis, settings.get('yhist_bin_size', None), *axis_mapping['y'], range_mode=range_mode,
                           selected=settings.get('yaxis1', None)),
    }


def histogram_edges(values, requested: str | float | None, axis: tuple, selected: str | None = None) -> dict | None:
    """The histogram page's bins: axis_bins for its one axis, with the bin edges spelled out (the last edge at
    the end of the range or past it, so the largest value is counted); None without values."""
    values = np.asarray(values, dtype=float)
    if not len(values):
        return None
    bins = axis_bins(values, requested, *axis, selected=selected)
    count = max(1, int(math.ceil((bins['end'] - bins['start']) / bins['size'])))
    edges = bins['start'] + bins['size'] * np.arange(count + 1)
    edges[-1] = max(edges[-1], bins['end'])
    bins['edges'] = edges.tolist()
    return bins


def density_data(graph_data: dict, axis_mapping: dict, settings) -> dict:
    """
    The density page's data from a scatter response (api.web2py.views.get_graph_data): the points with a
    value on both axes, the bins of each axis, the colour scale, the histograms toggle, and the axes with
    the log decision made (a logarithmic axis needs every value positive).
    """
    names, xaxis, yaxis = valid_points(graph_data['outputs'])
    axes = {axis: dict(axis_data) for axis, axis_data in graph_data['axes'].items()}
    bins = marginal_bins(xaxis, yaxis, axis_mapping, settings)
    if len(xaxis):
        axes['xaxis']['log'] = bool(axes['xaxis']['log'] and np.all(xaxis > 0))
        axes['yaxis']['log'] = bool(axes['yaxis']['log'] and np.all(yaxis > 0))
    color_palette, scale, histogram_color = color_scale(settings.get('color_palette', None))
    return dict(
        labels=graph_data['labels'],
        star_count=graph_data['star_count'],
        planet_count=graph_data['planet_count'],
        is_loggable=graph_data['is_loggable'],
        axes=axes,
        outputs={'name': names, 'xaxis': xaxis.tolist(), 'yaxis': yaxis.tolist()},
        bins=bins,
        show_xyhist=is_true_str(settings.get('show_xyhist', 'false')),
        color_palette=color_palette,
        color_scale=scale,
        histogram_color=histogram_color,
        bin_tags=BIN_TAGS,
    )
