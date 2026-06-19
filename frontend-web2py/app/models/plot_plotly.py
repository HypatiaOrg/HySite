from warnings import warn
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
    "viridis": "Viridis",
    "plasma": "Plasma",
    "cividis": "Cividis",
    "inferno": "Inferno",
    "magma": "Magma",
    "turbo": "Turbo"
}

plotly_colors = {
    "Viridis": "#440154",
    "Plasma": "#0d0887",
    "Inferno": "#000004",
    "Magma": "#000004",
    "Cividis": "#00224e",
    "Turbo": "#30123b"
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


def get_bin_width(hist_bin_size, one_axis: np.ndarray, one_range: float, label: str) -> float:
    #returns the actual bin with in data units, so we can directly set xbins.size and ybins.size
    try:
        bin_width = float(hist_bin_size)
    except (ValueError, TypeError):
        mode = bin_argument(hist_bin_size)
        if mode == 'error':
            # can be None if no error is defined for the label
            bin_width = get_error(label)
        else:
            # This sets the default bin size to the standard deviation of the data
            bin_width = np.std(one_axis)
    return check_bin_size(bin_width, one_range)

def get_axis_range(data: np.ndarray, range_mode:str = "full data",
                   sigma: float = 4, manual_min: float | None = None,
                   manual_max: float | None = None) -> tuple[float, float]:
    #chooses the visible plotting range
    #Options: full data, std dev (show mean +_ sigma * standard deviation, and manual)
    #Will need a place to input the sigma value, right now it is set to 4
    data = np.asarray(data, dtype=float)
    if range_mode == "manual" and manual_min is not None and manual_max is not None:
        return float(manual_min), float(manual_max)
    if range_mode == "std dev" :
        mean = np.mean(data)
        stdev = np.std(data)
        return mean - sigma * stdev, mean + sigma * stdev
    return float(np.min(data)), float(np.max(data))

def get_hist_color(color_scale):
    #uses the selected colormap to change the histogram color
    if isinstance(color_scale, list):
        return color_scale [0][1]
    return plotly_colors.get(color_scale, "#4e11b7")

def create_plotly_hist(name: list[str],
                       xaxis: list[str | float | int], yaxis: list[str | float | int],
                       x_label: str = None, y_label: str = None,
                       star_count: int = None, planet_count: int = None,
                       do_xlog: bool = False, do_ylog: bool = False,
                       xaxisinv: bool = False, yaxisinv: bool = False,
                       do_gridlines: bool = False,
                       show_xyhist: bool = True,
                       xhist_bin_size: float | str = bin_tags[0], yhist_bin_size: float | str = bin_tags[0],
                       color_pallet: str = "hypatia", range_mode: str = "full data", sigma: float = 4,
                       manual_xmin: float | None = None, manual_xmax: float | None = None,
                       manual_ymin: float | None = None, manual_ymax: float | None = None,
                       ) -> str:
    # Created plotly heatmap with optional marginal histograms
    xaxis = np.asarray(xaxis, dtype = float)
    yaxis = np.asarray(yaxis, dtype = float)

    valid = np.isfinite(xaxis) & np.isfinite(yaxis)
    xaxis = xaxis[valid]
    yaxis = yaxis[valid]

    if len(xaxis) == 0 or len(yaxis) == 0:
        raise ValueError("No valid data available for plotting")

    #Selects data range
    range_min_x, range_max_x = get_axis_range(
        xaxis, range_mode = range_mode, sigma = sigma, manual_min = manual_xmin, manual_max = manual_xmax
    )

    range_min_y, range_max_y = get_axis_range(
        yaxis, range_mode=range_mode, sigma = sigma, manual_min = manual_ymin, manual_max = manual_ymax
    )

    range_x = range_max_x - range_min_x
    range_y = range_max_y - range_min_y

    #Converts input bin choices into actual bin widths
    width_x = get_bin_width(
        hist_bin_size = xhist_bin_size, one_axis = xaxis,
        one_range = range_x, label = x_label
    )

    width_y = get_bin_width(
        hist_bin_size = yhist_bin_size, one_axis = yaxis,
        one_range = range_y, label = y_label
    )

    color_continuous_scale = color_pallets.get(color_pallet, color_pallets[default_color_pallet])
    histogram_color = get_hist_color(color_continuous_scale)

    warn(
        f"Plot: show_xyhist = {show_xyhist},"
        f"xbin = {xhist_bin_size}, ybin = {yhist_bin_size},"
        f"width_x = {width_x}, width_y = {width_y},"
        f"range_mode = {range_mode}, pallet = {color_pallet},"
    )

    #CASE 1 (heatmap with marginal histograms)
    if show_xyhist:
        fig = make_subplots(
            rows = 2, cols = 2, column_widths = [0.8, 0.2], row_heights = [0.2, 0.8],
            shared_xaxes = True, shared_yaxes = True, horizontal_spacing = 0.008, vertical_spacing = 0.008,
            specs = [
                [{"type": "histogram"}, None],
                [{"type": "histogram2d"}, {"type": "histogram"}]
            ]
        )

        #top histogram
        fig.add_trace(
            go.Histogram(
                x = xaxis, xbins = dict(start = range_min_x, end = range_max_x, size = width_x),
                marker = dict(color = histogram_color, line = dict(color = "black", width = 1)),
                showlegend = False,
            ),
            row=1, col=1
        )

        #side histogram
        fig.add_trace(
            go.Histogram(
                y = yaxis, ybins = dict(start = range_min_y, end = range_max_y, size = width_y),
                marker = dict(color = histogram_color, line = dict(color = "black", width = 1)),
                showlegend = False,
            ),
            row=2, col=2
        )

        #main heatmap
        fig.add_trace(
            go.Histogram2d(
                x = xaxis, y = yaxis, xbins = dict(start = range_min_x, end = range_max_x, size = width_x),
                ybins = dict(start = range_min_y, end = range_max_y, size = width_y),
                colorscale = color_continuous_scale, colorbar = dict(title = 'Frequency'),
                showscale = True
            ),
            row=2, col=1
        )

        fig.update_xaxes(title_text = x_label, row=2, col=1)
        fig.update_yaxes(title_text = y_label, row=2, col=1)

    #CASE 2: heatmap only
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Histogram2d(
                x = xaxis, y = yaxis, xbins = dict(start = range_min_x, end = range_max_x, size = width_x),
                ybins = dict(start = range_min_y, end = range_max_y, size = width_y),
                colorscale = color_continuous_scale, colorbar = dict(title = 'Frequency'),
                showscale = True
            )
        )

        fig.update_xaxes(title_text = x_label)
        fig.update_yaxes(title_text = y_label)

    #formatting
    fig.update_layout(
        width = 750,
        height = 650,
        plot_bgcolor = '#E5ECF6',
        paper_bgcolor = 'white',
        bargap=0.05,
        showlegend=False,
        title = None
    )


    #axis toggles and specific formatting
    if show_xyhist:
        #side hist
        fig.update_xaxes(
            type="log" if do_xlog and np.all(xaxis > 0) else "linear",
            autorange="reversed" if xaxisinv else True,
            showgrid=True,
            gridcolor="white",
            gridwidth=1,

            showline = True, linewidth=1, linecolor="black",
            mirror = True, ticks = "outside", ticklen = 6, tickwidth = 1,
            row=2, col=1
        )

        fig.update_yaxes(
            type="log" if do_ylog and np.all(yaxis > 0) else "linear",
            autorange="reversed" if yaxisinv else True,
            showgrid=True,
            gridcolor="white",
            gridwidth=1,

            showline=True, linewidth=1, linecolor="black",
            mirror=True, ticks="outside", ticklen=6, tickwidth=1,
            row=2, col=1
        )
        #top hist
        fig.update_xaxes(
            type="log" if do_xlog and np.all(xaxis > 0) else "linear",
            autorange="reversed" if xaxisinv else True,
            showgrid=True,
            gridcolor="white",
            gridwidth=1,
            row=1, col=1
        )

        fig.update_yaxes(
            autorange = True, showgrid = do_gridlines,
            row=1, col=1
        )

        fig.update_yaxes(
            type="log" if do_ylog and np.all(yaxis > 0) else "linear",
            autorange="reversed" if yaxisinv else True,
            showgrid=True,
            gridcolor="white",
            gridwidth=1,
            row=2, col=2
        )

        fig.update_xaxes(
            autorange = True, showgrid = do_gridlines,
            row=2, col=2
        )

    else:
        fig.update_xaxes(
            type = "log" if do_xlog else "linear",
            autorange = "reversed" if xaxisinv else True,
            showgrid = False,
            gridwidth = 1,
            showline=True, linewidth=2, linecolor="black",
            mirror=True, ticks="outside", ticklen=6, tickwidth=1
        )

        fig.update_yaxes(
            type = "log" if do_ylog else "linear",
            autorange = "reversed" if yaxisinv else True,
            showgrid = False,
            gridwidth = 1,
            showline=True, linewidth=2, linecolor="black",
            mirror=True, ticks="outside", ticklen=6, tickwidth=1
        )


    return fig.to_html(include_plotlyjs=True)
