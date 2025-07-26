from datetime import datetime

import numpy as np

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Viridis256
from bokeh.models import HoverTool, ColumnDataSource, ColorBar, LinearColorMapper, LogColorMapper, CustomJS, Label

hypatia_purple = '#4E11B7'
axis_lab_font_size = '12pt'
axis_lab_font_style = 'normal'
TOOLS = 'crosshair,pan,wheel_zoom,zoom_in,zoom_out,box_zoom,undo,redo,reset,tap,save,box_select,poly_select,lasso_select,'

plot_layers = ['all_hypatia', 'or_matches', 'combined_matches']

def bokeh_export_html(p):
    script, div = components(p)
    return script, div


def bokeh_default_settings(p, x_label: str = None, y_label: str = None, do_gridlines: bool = True):
    # toggle gridlines
    if not do_gridlines:
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
    # Format the axis labels
    if x_label:
        p.xaxis.axis_label = x_label.replace('_', ' ')
    if y_label:
        p.yaxis.axis_label = y_label.replace('_', ' ')
    # font settings
    p.xaxis.axis_label_text_font_size = axis_lab_font_size
    p.xaxis.axis_label_text_font_style = axis_lab_font_style
    p.xaxis.major_label_text_font_size = axis_lab_font_size
    p.xaxis.major_label_text_font_style = axis_lab_font_style
    p.yaxis.axis_label_text_font_size = axis_lab_font_size
    p.yaxis.axis_label_text_font_style = axis_lab_font_style
    p.yaxis.major_label_text_font_size = axis_lab_font_size
    p.yaxis.major_label_text_font_style = axis_lab_font_style
    return bokeh_export_html(p=p)


def create_bokeh_scatter(name: list[str],
                         xaxis: list[str | float | int], yaxis: list[str | float | int], zaxis: list[str | float | int],
                         x_label: str = None, y_label: str = None, z_label: str = None,
                         star_count: int = None, planet_count: int = None,
                         do_xlog: bool = False, do_ylog: bool = False, do_zlog: bool = False,
                         xaxisinv: bool = False, yaxisinv: bool = False, zaxisinv: bool = False,
                         has_zaxis: bool = False, do_gridlines: bool = False,
                         ):
    # if there is no data, then return a message
    if not xaxis:
        return '', 'No data points to display'
    bokeh_source = {'name': name}
    labels = {}
    if xaxis:
        xaxis = np.array(xaxis)
        bokeh_source['xaxis'] = xaxis
        labels['xaxis'] = x_label if x_label else 'X Axis'
    if yaxis:
        yaxis = np.array(yaxis)
        bokeh_source['yaxis'] = yaxis
        labels['yaxis'] = y_label if y_label else 'Y Axis'
    if zaxis and has_zaxis:
        zaxis = np.array(zaxis)
        bokeh_source['zaxis'] = zaxis
        labels['zaxis'] = z_label if z_label else 'Z Axis'
    # handle tooltips
    source = ColumnDataSource(bokeh_source)
    tooltips = "<b>@name</b><br/><div style='max-width:300px'>" + ', '.join(
        [labels[axis] + ' = @' + axis + '{0.00}' for axis in set(labels)]) + '</div>'
    hover = HoverTool(tooltips=tooltips)
    # build the bounds
    x_min = min(xaxis)
    x_max = max(xaxis)
    if x_min == x_max:
        x_min -= 1
        x_max += 1
    y_min = min(yaxis)
    y_max = max(yaxis)
    if y_min == y_max:
        y_min -= 1
        y_max += 1
    x_diff = x_max - x_min
    y_diff = y_max - y_min
    x_margin = 0.10 * x_diff
    y_margin = 0.10 * y_diff
    x_range = [x_min - x_margin, x_max + x_margin]
    y_range = [y_min - y_margin, y_max + y_margin]
    # set the axis type: log or linear
    if do_xlog:
        x_axis_type = 'log'
        x_array = np.array(xaxis)
        x_range[0] = np.min(x_array[x_array > 0])
    else:
        x_axis_type = 'linear'
    if do_ylog:
        y_axis_type = 'log'
        y_array = np.array(yaxis)
        y_range[0] = np.min(y_array[y_array > 0])
    else:
        y_axis_type = 'linear'
    # invert the axis if necessary
    if xaxisinv:
        x_range = x_range[::-1]
    if yaxisinv:
        y_range = y_range[::-1]
    # build the figure
    p = figure(tools=[TOOLS, hover], width=750, height=625,
               x_range=x_range,
               y_range=y_range,
               x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    if planet_count is not None:
        p.title.text = f'{planet_count} planets selected from {star_count} stars'
    else:
        p.title.text = f'{star_count} stars selected'
    p.title.align = 'center'

    # z-axis
    if has_zaxis:
        palette = Viridis256
        # invert the z-axis if necessary
        if zaxisinv:
            palette = palette[::-1]
        # set up a log scale if necessary
        if do_zlog:
            mapper = LogColorMapper(palette=palette, low=min(zaxis), high=max(zaxis))
        else:
            mapper = LinearColorMapper(palette=palette, low=min(zaxis), high=max(zaxis))
        # build the scatter plot
        p.scatter('xaxis', 'yaxis', fill_color={'field': 'zaxis', 'transform': mapper},
                  line_color={'field': 'zaxis', 'transform': mapper},
                  fill_alpha=0.3, line_alpha=0.8, source=source, size=8)
        color_bar = ColorBar(color_mapper=mapper, height=100, title=labels['zaxis'].replace('_', ' '),
                             border_line_width=1,
                             border_line_color='#cccccc', label_standoff=7)
        p.add_layout(color_bar)
    else:
        # build the scatter plot
        p.scatter('xaxis', 'yaxis',
                  fill_color=hypatia_purple, line_color=hypatia_purple, fill_alpha=0.3, line_alpha=0.6,
                  source=source, size=8)

    # callback
    callback = CustomJS(args={'allPlotData': source}, code="""
            const inds = cb_obj.indices;
            const d1 = allPlotData.data;
            const result = inds.map(i => d1['name'][i]);
            $("#star_list").val(result.join(","));
            $("select[name='star_action']").val("only");
            $("select[name='star_source']").val("hip")
        """)
    source.selected.js_on_change('indices', callback)

    # citation
    citation = Label(x=10, y=10, x_units='screen', y_units='screen',
                     text='Hypatia Catalog ' + datetime.now().strftime('%Y-%m-%d'),
                     text_alpha=0.5)
    p.add_layout(citation)
    return bokeh_default_settings(p=p, x_label=labels['xaxis'], y_label=labels['yaxis'], do_gridlines=do_gridlines)


def init_plot_data(**kwargs):
    return {
        'x': [], 'y': [], 'handles': [], 'names': [],
        'color': kwargs.get('color', default_color),
        'fill_alpha': kwargs.get('fill_alpha', default_fill_alpha),
        'line_alpha': kwargs.get('line_alpha', default_line_alpha),
        'label': kwargs.get('title', default_label),
        'marker': kwargs.get('marker', default_marker),
    }

def add_plot_data(plot_data, x_point, y_point, target_handle, star_name):
    plot_data['x'].append(x_point)
    plot_data['y'].append(y_point)
    plot_data['handles'].append(target_handle)
    plot_data['names'].append(star_name)
    return plot_data


def create_bokeh_targets(name: list[str],
                         xaxis: list[str | float | int], yaxis: list[str | float | int], 
                         target_handles: list[list[str]],
                         x_label: str = None, y_label: str = None,
                         do_xlog: bool = False, do_ylog: bool = False,
                         xaxisinv: bool = False, yaxisinv: bool = False,
                         do_gridlines: bool = False,
                         show_all_hypatia: bool = False, do_or_logic: bool = False,
                         requested_handles: list[str] = None,
                         ):
    requested_handles_set = set(requested_handles)
    # build the bounds
    x_min = min(xaxis)
    x_max = max(xaxis)
    if x_min == x_max:
        x_min -= 1
        x_max += 1
    y_min = min(yaxis)
    y_max = max(yaxis)
    if y_min == y_max:
        y_min -= 1
        y_max += 1
    x_diff = x_max - x_min
    y_diff = y_max - y_min
    x_margin = 0.10 * x_diff
    y_margin = 0.10 * y_diff
    x_range = [x_min - x_margin, x_max + x_margin]
    y_range = [y_min - (3.0 * y_margin), y_max + y_margin]
    # set the axis type: log or linear
    if do_xlog:
        x_axis_type = 'log'
        x_array = np.array(xaxis)
        x_range[0] = np.min(x_array[x_array > 0])
    else:
        x_axis_type = 'linear'
    if do_ylog:
        y_axis_type = 'log'
        y_array = np.array(yaxis)
        y_range[0] = np.min(y_array[y_array > 0])
    else:
        y_axis_type = 'linear'
    # invert the axis if necessary
    if xaxisinv:
        x_range = x_range[::-1]
    if yaxisinv:
        y_range = y_range[::-1]

    # if there is no data, then return a message
    number_of_targets = 0
    def sort_key(target_handle):
        # sort by x, then y, then target_handle, then star_name
        found_target_handles = requested_handles_set & set(target_handle)
        score = len(found_target_handles)
        for handle in found_target_handles:
            score += 0.01 * (requested_handles.index(handle))
        return score

    scores = [sort_key(target_handle) for target_handle in target_handles]
    # group the target types
    grouped_targets = {}
    for _score, x_point, y_point, target_handle, star_name in sorted(zip(scores, xaxis, yaxis, target_handles, name)):
        target_set = set(target_handle)
        if do_or_logic:
            if target_set.isdisjoint(requested_handles):
                if show_all_hypatia:
                    if 'all_hypatia' not in grouped_targets.keys():
                        grouped_targets['all_hypatia'] = init_plot_data(**all_hypatia_plot_options)
                    grouped_targets['all_hypatia'] = add_plot_data(grouped_targets['all_hypatia'], x_point, y_point,
                                                                   target_handle, star_name)
            else:
                if 'or_matches' not in grouped_targets.keys():
                    grouped_targets['or_matches'] = init_plot_data(**or_matches_plot_options)
                # if we are doing OR logic, then we only add the point to the source if it matches the requested handles
                grouped_targets['or_matches'] = add_plot_data(grouped_targets['or_matches'], x_point, y_point,
                                                              target_handle, star_name)
                number_of_targets += 1
        else:
            handles_found = set()
            for requested_handle in requested_handles:
                if requested_handle in target_set:
                    handles_found.add(requested_handle)
            if len(handles_found) == 0:
                if show_all_hypatia:
                    if 'all_hypatia' not in grouped_targets.keys():
                        grouped_targets['all_hypatia'] = init_plot_data(**all_hypatia_plot_options)
                    grouped_targets['all_hypatia'] = add_plot_data(grouped_targets['all_hypatia'], x_point, y_point,
                                                                  target_handle, star_name)
            elif len(handles_found) == 1:
                single_handle = list(handles_found)[0]
                if single_handle not in grouped_targets.keys():
                    grouped_targets[single_handle] = init_plot_data(**targets_metadata.get(single_handle, {}))
                grouped_targets[single_handle] = add_plot_data(grouped_targets[single_handle], x_point, y_point,
                                                               target_handle, star_name)
                number_of_targets += 1
            elif requested_handles_set.issubset(handles_found):
                if 'combined_matches' not in grouped_targets.keys():
                    grouped_targets['combined_matches'] = init_plot_data(**combined_matches_plot_options)
                grouped_targets['combined_matches'] = add_plot_data(grouped_targets['combined_matches'], x_point,
                                                                    y_point, target_handle, star_name)
                number_of_targets += 1
            else:
                if 'partial_matches' not in grouped_targets.keys():
                    grouped_targets['partial_matches'] = init_plot_data(**partial_matches_plot_options)
                grouped_targets['partial_matches'] = add_plot_data(grouped_targets['partial_matches'], x_point,
                                                                    y_point, target_handle, star_name)
                number_of_targets += 1

    if len(grouped_targets) == 0:
        return '', 'No data points to display'
    labels = {
        'xaxis':  x_label if x_label else 'X Axis',
        'yaxis':  y_label if y_label else 'Y Axis',
    }
    tooltips = "<b>@names</b><br/><div style='max-width:300px'>" + ', '.join(
        [labels[axis] + ' = @' + axis[0] + '{0.00}' for axis in set(labels)]) + '</div>'
    hover = HoverTool(tooltips=tooltips)
    # The Target Plot
    p = figure(tools=[TOOLS, hover], width=750, height=625,
               x_range=x_range,
               y_range=y_range,
               x_axis_type=x_axis_type, y_axis_type=y_axis_type)
    p.title.text = f'{number_of_targets} Targets selected'
    p.title.align = 'center'
    p.add_layout(Label(x=10, y=10, x_units='screen', y_units='screen',
                     text='Hypatia Catalog ' + datetime.now().strftime('%Y-%m-%d'),
                     text_alpha=0.5))
    for group_name, plot_data in grouped_targets.items():
        # handle tooltips
        source = ColumnDataSource(dict(
            x=np.array(plot_data['x']),
            y=np.array(plot_data['y']),
            names=plot_data['names'],
            handles=plot_data['handles'],
        ))
        # build the scatter plot
        p.scatter(f'x', 'y',
                  fill_color=plot_data['color'] , line_color=plot_data['color'] ,
                  fill_alpha=plot_data['fill_alpha'], line_alpha=plot_data['line_alpha'],
                  legend_label=plot_data['label'],
                  marker=plot_data['marker'],
                  source=source, size=8)
        # callback
        callback = CustomJS(args={'allPlotData': source}, code="""
                const inds = cb_obj.indices;
                const d1 = allPlotData.data;
                const result = inds.map(i => d1['names'][i]);
                $("#star_list").val(result.join(","));
                $("select[name='star_action']").val("only");
                $("select[name='star_source']").val("hip")
            """)
        source.selected.js_on_change('indices', callback)
    p.legend.location = 'bottom_right'
    p.legend.nrows=3
    p.legend.background_fill_alpha = 0.3
    leg = p.legend[0]
    leg.click_policy = 'hide'
    return bokeh_default_settings(p=p, x_label=labels['xaxis'], y_label=labels['yaxis'], do_gridlines=do_gridlines)


def create_bokeh_hist(hist_all, hist_planet, edges, x_data: list[str | float | int],
                      x_label: str = None,
                      normalize: bool = False, xaxisinv: bool = False, do_gridlines: bool = False,
                      ):
    # histogram - compare all data to the stars with planets
    if x_data:
        labels = {'xaxis': x_label if x_label else 'X Axis'}
    else:
        # if there is no data, then return a message
        return '', 'No data points to display'

    max_hist_all = float(max(hist_all))
    # normalize if necessary
    if normalize:
        y_label = 'Relative Frequency'
        labels['yaxis'] = y_label
        fill_alpha = 0.5
        line_alpha = 0.2
    else:
        y_label = 'Number of Stellar Systems'
        labels['yaxis'] = y_label
        fill_alpha = 1
        line_alpha = 1
    # set the bounds of the plot
    x_min = min(x_data)
    x_max = max(x_data)
    x_range = [x_min, x_max]
    # invert the plot if necessary
    if xaxisinv:
        x_range = x_range[::-1]
    # build the plot object
    p = figure(tools=[TOOLS], width=750, height=625,
               x_range=x_range,
               y_range=[0, max_hist_all * 1.20])
    p.quad(top=hist_all, bottom=0, left=edges[:-1], right=edges[1:],
           fill_color='maroon', line_color='black', fill_alpha=fill_alpha, line_alpha=line_alpha,
           legend_label='All Hypatia')
    p.quad(top=hist_planet, bottom=0, left=edges[:-1], right=edges[1:],
           fill_color='orange', line_color='black', fill_alpha=fill_alpha, line_alpha=line_alpha,
           legend_label='Exo-Hosts')
    # citation
    citation = Label(x=10, y=10, x_units='screen', y_units='screen',
                     text='Hypatia Catalog ' + datetime.now().strftime('%Y-%m-%d'),
                     text_alpha=0.5)
    p.add_layout(citation)
    return bokeh_default_settings(p=p, x_label=x_label, y_label=y_label, do_gridlines=do_gridlines)