"""
The density map: a Plotly heat map of the scatter page's points, with histograms along the axes. The API
decided the points, the range and bin width of each axis, the colour scale and the axes
(api.web2py.density); this only draws.
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_plotly_density(xaxis: list[float], yaxis: list[float],
                          x_bins: dict | None, y_bins: dict | None,
                          color_scale: list | str, histogram_color: str,
                          x_label: str = None, y_label: str = None,
                          do_xlog: bool = False, do_ylog: bool = False,
                          xaxisinv: bool = False, yaxisinv: bool = False,
                          do_gridlines: bool = False, show_xyhist: bool = True,
                          ) -> str:
    """The figure as HTML. x_bins and y_bins are the API's start, end and size of each axis's bins."""
    # if there is no data, then return a message
    if not xaxis or not x_bins or not y_bins:
        return 'No data points to display'
    xaxis = np.asarray(xaxis, dtype=float)
    yaxis = np.asarray(yaxis, dtype=float)
    xbins = dict(start=x_bins['start'], end=x_bins['end'], size=x_bins['size'])
    ybins = dict(start=y_bins['start'], end=y_bins['end'], size=y_bins['size'])
    histogram_marker = dict(color=histogram_color, line=dict(color="black", width=1))

    # CASE 1 (heatmap with marginal histograms)
    if show_xyhist:
        fig = make_subplots(
            rows=2, cols=2, column_widths=[0.8, 0.2], row_heights=[0.2, 0.8],
            shared_xaxes=True, shared_yaxes=True, horizontal_spacing=0.008, vertical_spacing=0.008,
            specs=[
                [{"type": "histogram"}, None],
                [{"type": "histogram2d"}, {"type": "histogram"}]
            ]
        )
        # top histogram
        fig.add_trace(go.Histogram(x=xaxis, xbins=xbins, marker=histogram_marker, showlegend=False), row=1, col=1)
        # side histogram
        fig.add_trace(go.Histogram(y=yaxis, ybins=ybins, marker=histogram_marker, showlegend=False), row=2, col=2)
        # main heatmap
        fig.add_trace(
            go.Histogram2d(
                x=xaxis, y=yaxis, xbins=xbins, ybins=ybins,
                colorscale=color_scale, colorbar=dict(title='Num of<br>Stars/Bin'), showscale=True
            ),
            row=2, col=1
        )
        fig.update_xaxes(title_text=x_label, row=2, col=1)
        fig.update_yaxes(title_text=y_label, row=2, col=1)

    # CASE 2: heatmap only
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Histogram2d(
                x=xaxis, y=yaxis, xbins=xbins, ybins=ybins,
                colorscale=color_scale, colorbar=dict(title='Num of<br>Stars/Bin'), showscale=True
            )
        )
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=y_label)

    # formatting
    fig.update_layout(
        width=750,
        height=650,
        plot_bgcolor='#E5ECF6',
        paper_bgcolor='white',
        bargap=0.05,
        showlegend=False,
        title=None
    )

    # axis toggles and specific formatting
    x_axis_type = "log" if do_xlog else "linear"
    y_axis_type = "log" if do_ylog else "linear"
    x_autorange = "reversed" if xaxisinv else True
    y_autorange = "reversed" if yaxisinv else True
    if show_xyhist:
        # the heatmap
        fig.update_xaxes(
            type=x_axis_type, autorange=x_autorange, showgrid=True, gridcolor="white", gridwidth=1,
            showline=True, linewidth=1, linecolor="black",
            mirror=True, ticks="outside", ticklen=6, tickwidth=1,
            row=2, col=1
        )
        fig.update_yaxes(
            type=y_axis_type, autorange=y_autorange, showgrid=True, gridcolor="white", gridwidth=1,
            showline=True, linewidth=1, linecolor="black",
            mirror=True, ticks="outside", ticklen=6, tickwidth=1,
            row=2, col=1
        )
        # top histogram
        fig.update_xaxes(
            type=x_axis_type, autorange=x_autorange, showgrid=True, gridcolor="white", gridwidth=1,
            row=1, col=1
        )
        fig.update_yaxes(autorange=True, showgrid=do_gridlines, row=1, col=1)
        # side histogram
        fig.update_yaxes(
            type=y_axis_type, autorange=y_autorange, showgrid=True, gridcolor="white", gridwidth=1,
            row=2, col=2
        )
        fig.update_xaxes(autorange=True, showgrid=do_gridlines, row=2, col=2)
    else:
        fig.update_xaxes(
            type=x_axis_type, autorange=x_autorange, showgrid=False, gridwidth=1,
            showline=True, linewidth=2, linecolor="black",
            mirror=True, ticks="outside", ticklen=6, tickwidth=1
        )
        fig.update_yaxes(
            type=y_axis_type, autorange=y_autorange, showgrid=False, gridwidth=1,
            showline=True, linewidth=2, linecolor="black",
            mirror=True, ticks="outside", ticklen=6, tickwidth=1
        )

    # the figure only: the page loads static/js/plotly.min.js once (frontend-web2py/Dockerfile)
    return fig.to_html(include_plotlyjs=False, full_html=False)
