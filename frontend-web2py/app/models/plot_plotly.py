"""
The plots: Plotly figures of what the API returns. The API decided the data, the target layers, the
histogram series, the density bins and the axes (api.web2py.plots, api.web2py.density); this only draws.
Each figure comes back as an HTML fragment holding the figure's data and layout; the page loads
static/js/plotly.min.js once (the copy bundled with the installed plotly package, see the Dockerfile).

Until October 2026 the scatter, targets and histogram plots were Bokeh figures (models/plot_bokeh.py).
Plotly draws them now, so the Next.js frontend (issue #19) can draw the same figures from the same data.
What the Bokeh plots did is kept: the hover text as a stacked column of every star under the cursor, the
z axis as a colour scale, the selected stars going to the star list, one legend entry per target layer
(click to hide), the normalized histogram, the "Hypatia Catalog" citation with the date, the figure size.
"""
import json
from datetime import datetime

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

hypatia_purple = '#4E11B7'
PLOT_WIDTH = 750
PLOT_MARGIN_LEFT = 70   # the figures' left margin: the y axis line is here (the pages' controls line up with it)
PLOT_HEIGHT = 625
AXIS_FONT_SIZE = 16  # pixels: the 12pt of the Bokeh plots
MARGIN = 0.10  # of the data range, on each side
# the Bokeh marker names of the catalog summary's target metadata, as Plotly symbols
MARKERS = {'circle': 'circle', 'square': 'square', 'diamond': 'diamond', 'triangle': 'triangle-up',
           'inverted_triangle': 'triangle-down', 'plus': 'cross', 'cross': 'cross', 'x': 'x', 'star': 'star',
           'asterisk': 'asterisk', 'square_pin': 'square', 'hex': 'hexagon', 'dot': 'circle', 'dash': 'line-ew'}
# a box or lasso selection sends the selected stars to the star list field, as the Bokeh plots did.
# The script runs after the figure's own script in the fragment; "text" holds the star names.
SELECT_SCRIPT = """
<script>
    (function() {
        var plot = document.getElementById("%(div_id)s");
        if (!plot || !plot.on) { return; }
        plot.on("plotly_selected", function(event) {
            if (!event) { return; }
            var names = event.points.filter(function(point) {
                return plot.data[point.curveNumber].type === "scattergl";  // not the histograms' bars
            }).map(function(point) {
                return (plot.data[point.curveNumber].text || [])[point.pointNumber];
            });
            $("#star_list").val(names.join(","));
            $("select[name='star_action']").val("only");
            $("select[name='star_source']").val("hip");
        });
    })();
</script>"""
# the hover labels: the stars within a few pixels of the cursor, stacked in columns that fill the window's
# height, as Bokeh's hover tool stacked them; the nearest 25, headed by "Showing 25 of N Stars" when there are more (Plotly's own hover shows one point per trace, and searches slowly over an SVG plot,
# so the figure has hovermode off and this script does the search over the traces' arrays instead)
HOVER_SCRIPT = """
<script>
    (function() {
        var plot = document.getElementById("%(div_id)s");
        if (!plot) { return; }
        var labels = %(labels)s, MAX_LABELS = 25, RADIUS = 4;  // pixels: a marker's radius (size 8)
        var types = {f8: Float64Array, f4: Float32Array, i4: Int32Array, i2: Int16Array, i1: Int8Array,
                     u4: Uint32Array, u2: Uint16Array, u1: Uint8Array};
        function values(column) {  // a plain list, or the base64 typed array Plotly's HTML holds
            if (Array.isArray(column)) { return column; }
            if (!column || !column.bdata) { return []; }
            var bytes = atob(column.bdata), buffer = new Uint8Array(bytes.length);
            for (var i = 0; i < bytes.length; i++) { buffer[i] = bytes.charCodeAt(i); }
            return new (types[column.dtype] || Float64Array)(buffer.buffer);
        }
        var cache = [];
        function columns(c) {  // the decoded arrays of a trace, decoded once
            var trace = plot.data[c];
            if (!cache[c] || cache[c].source !== trace.x) {
                cache[c] = {source: trace.x, x: values(trace.x), y: values(trace.y),
                            z: trace.customdata ? values(trace.customdata) : null, names: trace.text || []};
            }
            return cache[c];
        }
        var label = document.createElement("div");
        label.style.cssText = "position:absolute; display:none; pointer-events:none; z-index:1000;" +
            "background:rgba(255,255,255,0.95); border:1px solid #888; border-radius:3px; padding:2px 6px;" +
            "font-size:12px; font-weight:normal; text-align:left; white-space:nowrap; line-height:1.3; color:#222";
        document.body.appendChild(label);
        function hide() { label.style.display = "none"; }
        function show(event) {
            var layout = plot._fullLayout;
            if (!layout || !layout.xaxis || !layout.xaxis.d2p) { hide(); return; }
            var box = plot.getBoundingClientRect();
            // pixels from the top left of the points' axes (with the histograms shown, the axes take part of the figure)
            var xa = layout.xaxis, ya = layout.yaxis, found = [];
            var px = event.clientX - box.left - xa._offset, py = event.clientY - box.top - ya._offset;
            if (px < 0 || py < 0 || px > xa._length || py > ya._length) { hide(); return; }
            for (var c = 0; c < plot.data.length; c++) {
                if (plot.data[c].type !== "scattergl") { continue; }  // the histograms' bars are not stars
                if (plot._fullData[c] && plot._fullData[c].visible !== true) { continue; }  // hidden from the legend
                var data = columns(c);
                for (var i = 0; i < data.x.length; i++) {
                    var dx = xa.d2p(data.x[i]) - px, dy = ya.d2p(data.y[i]) - py, d = dx * dx + dy * dy;
                    if (d <= RADIUS * RADIUS) { found.push([d, c, i]); }
                }
            }
            if (!found.length) { hide(); return; }
            found.sort(function(a, b) { return a[0] - b[0]; });
            var items = [];
            if (found.length > MAX_LABELS) {
                items.push("<div style='padding:2px 0; color:#666'>Showing " + MAX_LABELS + " of " + found.length + " Stars</div>");
            }
            for (var k = 0; k < found.length && k < MAX_LABELS; k++) {
                var data = columns(found[k][1]), i = found[k][2];
                var text = labels.x + " = " + Number(data.x[i]).toFixed(2) + ", " + labels.y + " = " + Number(data.y[i]).toFixed(2);
                if (data.z && labels.z) { text += ", " + labels.z + " = " + Number(data.z[i]).toFixed(2); }
                items.push("<div style='padding:2px 0; border-top:1px solid #ddd'><b>" +
                           $("<span>").text(data.names[i] || "").html() + "</b><br/>" + $("<span>").text(text).html() + "</div>");
            }
            // the labels in columns: one column fills the height of the window, the next starts beside it
            function column(cells) { return "<div style='display:inline-block; vertical-align:top; padding:0 6px'>" + cells.join("") + "</div>"; }
            label.innerHTML = column(items.slice(0, 1));
            label.style.display = "block";
            var itemHeight = label.firstChild.firstChild.offsetHeight || 34;  // measured on the first item
            var perColumn = Math.max(1, Math.floor((window.innerHeight - 24) / itemHeight));
            var blocks = [];
            for (var start = 0; start < items.length; start += perColumn) { blocks.push(column(items.slice(start, start + perColumn))); }
            label.innerHTML = blocks.join("");
            // next to the cursor, kept inside the window
            var top = Math.min(event.pageY + 12, window.scrollY + window.innerHeight - label.offsetHeight - 4);
            var left = event.pageX + 12;
            if (event.clientX + 12 + label.offsetWidth > window.innerWidth) { left = Math.max(window.scrollX + 4, event.pageX - 12 - label.offsetWidth); }
            label.style.top = Math.max(window.scrollY + 4, top) + "px";
            label.style.left = left + "px";
        }
        var pending = null;
        plot.addEventListener("mousemove", function(event) {  // once per frame, not once per mouse event
            pending = event;
            window.requestAnimationFrame(function() { if (pending) { show(pending); pending = null; } });
        });
        plot.addEventListener("mouseleave", hide);
    })();
</script>"""


def axis_range(values: np.ndarray, do_log: bool = False, inverse: bool = False,
               low_margin: float = MARGIN, high_margin: float = MARGIN) -> tuple[list[float], str]:
    """The range and type of an axis: the data with a margin on each side; a log axis starts at the smallest
    positive value (its range in powers of ten, as Plotly wants it) and is linear when no value is positive."""
    v_min, v_max = float(np.min(values)), float(np.max(values))
    if v_min == v_max:
        v_min -= 1
        v_max += 1
    diff = v_max - v_min
    low, high = v_min - low_margin * diff, v_max + high_margin * diff
    axis_type = 'linear'
    if do_log:
        positive = values[values > 0]
        if len(positive):
            low, high = np.log10(float(np.min(positive))), np.log10(max(high, float(np.max(positive))))
            axis_type = 'log'
    return ([high, low] if inverse else [low, high]), axis_type


def axis_style(label: str | None, do_gridlines: bool, **kwargs) -> dict:
    """What every axis gets: the label (underscores as spaces), the font size, the gridlines toggle."""
    return dict(title=dict(text=label.replace('_', ' ') if label else None, font=dict(size=AXIS_FONT_SIZE)),
                tickfont=dict(size=AXIS_FONT_SIZE), showgrid=do_gridlines, gridcolor='#e5e5e5', zeroline=False,
                showline=True, linecolor='black', ticks='outside', **kwargs)


# the toolbar: Plotly's "Zoom" is the drag-a-rectangle zoom, which the Bokeh toolbar called "Box Zoom", and visitors
# looked for that name (issue #35): a locale with that one entry, the other tooltips keep Plotly's text. No
# "Share chart..." button: it uploads the figure to Plotly's web service, which is not this site's business
PLOT_CONFIG = dict(locale='en-hypatia', locales={'en-hypatia': {'dictionary': {'Zoom': 'Box zoom: drag a rectangle'}}},
                   modeBarButtonsToRemove=['sendChartToCloud'], showSendToCloud=False)


# the histograms along the axes of the scatter and targets plots: the points keep the lower left of the figure,
# the histograms take a strip above and beside them, on the same x and y axes
POINTS_DOMAIN = [0, 0.78]
HISTOGRAM_DOMAIN = [0.8, 1]
HISTOGRAM_OPACITY = 0.5   # the targets' histograms, one per list, drawn over each other


def plotly_bins(bins: dict | None, axis_type: str) -> dict | None:
    """An axis's bins as Plotly wants them, or None for Plotly's own bins: the API's bins are in data units,
    which a logarithmic axis cannot use."""
    if not bins or axis_type == 'log':
        return None
    return dict(start=bins['start'], end=bins['end'], size=bins['size'])


def add_marginal_histograms(fig: go.Figure, series: list[dict], bins: dict | None, x_type: str, y_type: str,
                            do_gridlines: bool, opacity: float = 1.0) -> None:
    """The histograms along the x and y axes: one pair per series (x, y, color, name), over each other when
    there are several. The points' axes shrink to POINTS_DOMAIN; the histograms' count axes take the rest."""
    bins = bins or {}
    x_bins, y_bins = plotly_bins(bins.get('xaxis'), x_type), plotly_bins(bins.get('yaxis'), y_type)
    for one in series:
        marker = dict(color=one['color'], line=dict(color='black', width=1))
        common = dict(marker=marker, opacity=opacity, name=one['name'], legendgroup=one['name'],
                      showlegend=False, hoverinfo='skip')
        fig.add_trace(go.Histogram(x=one['x'], xbins=x_bins, yaxis='y2', **common))
        fig.add_trace(go.Histogram(y=one['y'], ybins=y_bins, xaxis='x2', **common))
    counts = dict(title=None, tickfont=dict(size=12), showgrid=do_gridlines, gridcolor='#e5e5e5', zeroline=False,
                  showline=True, linecolor='black', ticks='outside', fixedrange=True)
    # the points' axes drawn on all four sides (mirror), so the points and the histograms are framed apart
    fig.update_layout(barmode='overlay', bargap=0,
                      xaxis=dict(domain=POINTS_DOMAIN, mirror=True), yaxis=dict(domain=POINTS_DOMAIN, mirror=True),
                      yaxis2=dict(domain=HISTOGRAM_DOMAIN, anchor='x', **counts),
                      xaxis2=dict(domain=HISTOGRAM_DOMAIN, anchor='y', **counts))


def plot_title(text: str) -> dict:
    """The title, over the left edge of the plot area: the toolbar lies along the top right (issue #35)."""
    return dict(text=text, xref='paper', x=0, xanchor='left')


def citation() -> dict:
    """The "Hypatia Catalog <date>" note in the bottom left corner."""
    return dict(text='Hypatia Catalog ' + datetime.now().strftime('%Y-%m-%d'), xref='paper', yref='paper',
                x=0, y=0, xanchor='left', yanchor='bottom', xshift=10, yshift=10, showarrow=False, opacity=0.5)


def figure_html(fig: go.Figure, div_id: str, hover_labels: dict[str, str] | None = None) -> str:
    """The figure as an HTML fragment (the page has plotly.min.js). With hover_labels (the axis labels for
    the hover text), the points plot gets the stacked hover labels and the selection into the star list."""
    fig.update_layout(width=PLOT_WIDTH, height=PLOT_HEIGHT, paper_bgcolor='white', plot_bgcolor='white',
                      margin=dict(l=PLOT_MARGIN_LEFT, r=30, t=50, b=60))
    if hover_labels:
        fig.update_layout(hovermode=False)
    html = fig.to_html(include_plotlyjs=False, full_html=False, div_id=div_id, config=PLOT_CONFIG)
    if hover_labels:
        labels = {axis[0]: label.replace('_', ' ') for axis, label in hover_labels.items()}
        html += SELECT_SCRIPT % dict(div_id=div_id)
        html += HOVER_SCRIPT % dict(div_id=div_id, labels=json.dumps(labels))
    return html


def create_plotly_scatter(name: list[str],
                          xaxis: list[float], yaxis: list[float], zaxis: list[float],
                          x_label: str = None, y_label: str = None, z_label: str = None,
                          star_count: int = None, planet_count: int = None,
                          do_xlog: bool = False, do_ylog: bool = False, do_zlog: bool = False,
                          xaxisinv: bool = False, yaxisinv: bool = False, zaxisinv: bool = False,
                          has_zaxis: bool = False, do_gridlines: bool = False,
                          bins: dict | None = None, show_hist: bool = False,
                          ) -> str:
    """The scatter plot; with a z axis, the points are coloured on a Viridis scale with a colour bar. With
    show_hist, histograms of the points along each axis (bins from the API, api.web2py.density)."""
    # if there is no data, then return a message
    if not xaxis:
        return 'No data points to display'
    xaxis = np.asarray(xaxis, dtype=float)
    yaxis = np.asarray(yaxis, dtype=float)
    labels = {'xaxis': x_label if x_label else 'X Axis', 'yaxis': y_label if y_label else 'Y Axis'}
    has_zaxis = bool(has_zaxis and len(zaxis))
    marker = dict(size=8, color=hypatia_purple, opacity=0.5, line=dict(color=hypatia_purple, width=1))
    customdata = None
    if has_zaxis:
        zaxis = np.asarray(zaxis, dtype=float)
        labels['zaxis'] = z_label if z_label else 'Z Axis'
        customdata = zaxis
        colorbar = dict(title=dict(text=labels['zaxis'].replace('_', ' '), side='right'), len=0.4, thickness=15,
                        outlinecolor='#cccccc', outlinewidth=1)
        # a log colour scale: the colours follow log10 of the value, the colour bar's ticks show the values
        if do_zlog and np.all(zaxis > 0):
            color = np.log10(zaxis)
            tick_powers = range(int(np.ceil(color.min())), int(np.floor(color.max())) + 1)
            colorbar.update(tickvals=list(tick_powers), ticktext=[f'{10.0 ** power:g}' for power in tick_powers])
        else:
            color = zaxis
        marker.update(color=color, colorscale='Viridis', reversescale=zaxisinv, showscale=True, colorbar=colorbar,
                      line=dict(width=0))
    # WebGL points: an SVG plot of ten thousand markers is slow to draw and to hover over
    fig = go.Figure(go.Scattergl(x=xaxis, y=yaxis, mode='markers', marker=marker, text=list(name),
                                 customdata=customdata, hoverinfo='skip', showlegend=False))
    x_range, x_type = axis_range(xaxis, do_log=do_xlog, inverse=xaxisinv)
    y_range, y_type = axis_range(yaxis, do_log=do_ylog, inverse=yaxisinv)
    fig.update_xaxes(range=x_range, type=x_type, **axis_style(labels['xaxis'], do_gridlines))
    fig.update_yaxes(range=y_range, type=y_type, **axis_style(labels['yaxis'], do_gridlines))
    if show_hist:
        add_marginal_histograms(fig, [dict(x=xaxis, y=yaxis, color=hypatia_purple, name='Stars')], bins,
                                x_type, y_type, do_gridlines)
    if planet_count is not None:
        title = f'{planet_count} planets selected from {star_count} stars'
    else:
        title = f'{star_count} stars selected'
    fig.update_layout(title=plot_title(title), annotations=[citation()])
    return figure_html(fig, div_id='scatter-plot', hover_labels=labels)


def create_plotly_targets(xaxis: list[float], yaxis: list[float],
                          layers: list[dict], number_of_targets: int,
                          x_label: str = None, y_label: str = None,
                          do_xlog: bool = False, do_ylog: bool = False,
                          xaxisinv: bool = False, yaxisinv: bool = False,
                          do_gridlines: bool = False,
                          bins: dict | None = None, show_hist: bool = False,
                          ) -> str:
    """The targets plot: one scatter trace per layer the API made (api.web2py.plots.group_targets), with a
    legend entry each; a click on an entry hides its layer. With show_hist, a histogram of each layer along
    each axis, in the layer's colour, drawn over each other (bins from the API, shared by the layers)."""
    if not layers:
        return 'No data points to display'
    xaxis = np.asarray(xaxis, dtype=float)
    yaxis = np.asarray(yaxis, dtype=float)
    labels = {'xaxis': x_label if x_label else 'X Axis', 'yaxis': y_label if y_label else 'Y Axis'}
    fig = go.Figure()
    for layer in layers:
        fig.add_trace(go.Scattergl(
            x=np.asarray(layer['x'], dtype=float), y=np.asarray(layer['y'], dtype=float), mode='markers',
            name=layer['label'], legendgroup=layer['label'], text=list(layer['names']), hoverinfo='skip',
            marker=dict(symbol=MARKERS.get(layer['marker'], 'circle'), size=8, color=layer['color'],
                        opacity=layer['fill_alpha'], line=dict(color=layer['color'], width=1)),
        ))
    # room below the points for the legend, as the Bokeh plot had
    x_range, x_type = axis_range(xaxis, do_log=do_xlog, inverse=xaxisinv)
    y_range, y_type = axis_range(yaxis, do_log=do_ylog, inverse=yaxisinv, low_margin=3 * MARGIN)
    fig.update_xaxes(range=x_range, type=x_type, **axis_style(labels['xaxis'], do_gridlines))
    fig.update_yaxes(range=y_range, type=y_type, **axis_style(labels['yaxis'], do_gridlines))
    if show_hist:
        add_marginal_histograms(fig, [dict(x=np.asarray(layer['x'], dtype=float), y=np.asarray(layer['y'], dtype=float),
                                           color=layer['color'], name=layer['label']) for layer in layers],
                                bins, x_type, y_type, do_gridlines, opacity=HISTOGRAM_OPACITY)
    fig.update_layout(
        title=plot_title(f'{number_of_targets} Targets selected'),
        legend=dict(orientation='h', x=1, xanchor='right', y=0, yanchor='bottom', bgcolor='rgba(255,255,255,0.3)',
                    itemclick='toggle', itemdoubleclick='toggleothers'),
        annotations=[citation()],
    )
    return figure_html(fig, div_id='targets-plot', hover_labels=labels)


def create_plotly_hist(series: list[dict], edges: list[float], x_range: list[float] | None,
                       x_label: str = None,
                       normalize: bool = False, xaxisinv: bool = False, do_gridlines: bool = False,
                       ) -> str:
    """The histogram: one bar series per entry the API made (api.web2py.plots.histogram_series), over the
    API's bin edges."""
    # if there is no data, then return a message
    if not x_range:
        return 'No data points to display'
    labels = {'xaxis': x_label if x_label else 'X Axis'}
    edges = np.asarray(edges, dtype=float)
    centres = (edges[:-1] + edges[1:]) / 2.0
    widths = np.diff(edges)
    max_hist_all = float(max(series[0]['counts']))
    # normalize if necessary
    if normalize:
        labels['yaxis'] = 'Relative Frequency'
        opacity = 0.5
    else:
        labels['yaxis'] = 'Number of Stellar Systems'
        opacity = 1.0
    fig = go.Figure()
    for one_series in series:
        fig.add_trace(go.Bar(
            x=centres, y=one_series['counts'], width=widths, name=one_series['label'], opacity=opacity,
            marker=dict(color=one_series['color'], line=dict(color='black', width=1)),
            customdata=np.column_stack([edges[:-1], edges[1:]]),
            hovertemplate=f"{labels['xaxis']} %{{customdata[0]:.2f}} to %{{customdata[1]:.2f}}<br>%{{y}}<extra>%{{fullData.name}}</extra>",
        ))
    # invert the plot if necessary
    x_range = list(x_range)
    if xaxisinv:
        x_range = x_range[::-1]
    fig.update_xaxes(range=x_range, **axis_style(labels['xaxis'], do_gridlines))
    fig.update_yaxes(range=[0, max_hist_all * 1.20], **axis_style(labels['yaxis'], do_gridlines))
    fig.update_layout(barmode='overlay', bargap=0, annotations=[citation()])
    return figure_html(fig, div_id='hist-plot')


def create_plotly_density(xaxis: list[float], yaxis: list[float],
                          x_bins: dict | None, y_bins: dict | None,
                          color_scale: list | str, histogram_color: str,
                          x_label: str = None, y_label: str = None,
                          do_xlog: bool = False, do_ylog: bool = False,
                          xaxisinv: bool = False, yaxisinv: bool = False,
                          do_gridlines: bool = False, show_xyhist: bool = True,
                          ) -> str:
    """The density map: a heat map of the points, with histograms along the axes when wanted. The API
    decided the points, the bins (start, end and size of each axis), the colours and the axes
    (api.web2py.density)."""
    # if there is no data, then return a message
    if not xaxis or not x_bins or not y_bins:
        return 'No data points to display'
    xaxis = np.asarray(xaxis, dtype=float)
    yaxis = np.asarray(yaxis, dtype=float)
    xbins = dict(start=x_bins['start'], end=x_bins['end'], size=x_bins['size'])
    ybins = dict(start=y_bins['start'], end=y_bins['end'], size=y_bins['size'])
    histogram_marker = dict(color=histogram_color, line=dict(color="black", width=1))
    # the colour bar lies under the plot, so the heat map keeps the width and shape of the other pages' plots;
    # centred under the heat map's column (80% of the width beside the side histogram, all of it without)
    heatmap_width = 0.8 if show_xyhist else 1.0
    colorbar = dict(title=dict(text='Number of stars per bin', side='bottom'), orientation='h',
                    x=heatmap_width / 2, xanchor='center', len=heatmap_width, y=-0.13, yanchor='top',
                    thickness=15, outlinecolor='#cccccc', outlinewidth=1)

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
        # (named after the axis, the hover text being the bin's count alone; the count is on y for the top
        # histogram and on x for the side one)
        fig.add_trace(go.Histogram(x=xaxis, xbins=xbins, marker=histogram_marker, showlegend=False,
                                   name=x_label or 'X', hovertemplate='%{y}'),
                      row=1, col=1)
        # side histogram
        fig.add_trace(go.Histogram(y=yaxis, ybins=ybins, marker=histogram_marker, showlegend=False,
                                   name=y_label or 'Y', hovertemplate='%{x}'),
                      row=2, col=2)
        # main heatmap
        fig.add_trace(
            go.Histogram2d(
                x=xaxis, y=yaxis, xbins=xbins, ybins=ybins, name='Density',
                colorscale=color_scale, colorbar=colorbar, showscale=True
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
                x=xaxis, y=yaxis, xbins=xbins, ybins=ybins, name='Density',
                colorscale=color_scale, colorbar=colorbar, showscale=True
            )
        )
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=y_label)

    # formatting
    fig.update_layout(
        width=PLOT_WIDTH,
        height=PLOT_HEIGHT,
        margin=dict(l=PLOT_MARGIN_LEFT, r=30, t=50, b=140),   # room under the x axis for the colour bar and its title
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
    return fig.to_html(include_plotlyjs=False, full_html=False, div_id='density-plot', config=PLOT_CONFIG)
