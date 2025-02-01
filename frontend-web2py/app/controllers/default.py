import os
import copy

import urllib.request
import numpy as np
from bokeh.plotting import figure, show, output_file, ColumnDataSource
from bokeh.models import HoverTool, ColumnDataSource, ColorBar, LinearColorMapper, LogColorMapper, CustomJS, Label
from bokeh.embed import components
from bokeh.palettes import Viridis3, Viridis256
from bokeh.io import export_png, export_svgs

import shelve
import uuid
import json
import random
import re
from datetime import datetime
import logging

from time import time

logging.basicConfig(filename='logging.log', level=logging.DEBUG)
# logging.warning("Test")


# -*- coding: utf-8 -*-
### required - do no delete
def user(): return dict(form=auth())


def download(): return response.download(request, db)


def call(): return service()


### end requires

# this is the front page
def index():
    webURL = urllib.request.urlopen(f'{BASE_API_URL}home/')
    return dict(counts=json.loads(webURL.read().decode(webURL.info().get_content_charset('utf-8'))))


def help():
    return dict()


def about():
    return dict()


def nea():
    return dict()


def credits():
    return dict()


def launch():
    requested_mode = request.vars.mode
    if isinstance(requested_mode, list):
        requested_mode = requested_mode[0]
    if requested_mode == 'hist':
        session.mode = 'hist'
    else:
        session.mode = 'scatter'
    # add default values for missing session variables
    for var_name, default_val in session_defaults_launch.items():
        session_value = session.__getattr__(var_name)
        if session_value is None:
            session[var_name] = default_val
    session['toggle_vars_to_load'] = {key for key in toggle_graph_vars if session[key]}
    # splitting of strings into lists
    if isinstance(session.tablecols, str):
        session.tablecols = session.tablecols.split(',')
    return dict()


def dropdown():
    return dict()


def error():
    return dict()


def set_request_values():
    return


def get_settings() -> dict[str, any]:
    # make changes to the graph settings based on the session values
    all_settings = {}
    for graph_var in exported_session_vars:
        session_value = session.__getattr__(graph_var)
        if graph_var == 'statistic':
            all_settings['return_median'] = session_value == 'median'
        else:
            all_settings[graph_var] = session_value
    return all_settings


def graph():
    all_request_vars = set(request.vars.keys())
    # set new session values (non-toggles controls) from the request
    for key in all_request_vars - toggle_graph_vars:
        session[key] = request.vars[key]
    # these values are toggled by the act of being requested (http POST), and the toggle action is controlled here
    bool_triggers = (all_request_vars & toggle_graph_vars) | session['toggle_vars_to_load']
    for key in bool_triggers:
        session[key] = True
    # these values are toggled by the act of not being, and the toggle action is control here
    bool_not_triggered = toggle_graph_vars - bool_triggers
    for key in bool_not_triggered:
        session[key] = False
    session['toggle_vars_to_load'] = set()
    # special parsing for lists as strings
    if (request.vars.graph_submit and not request.vars.catalogs):
        session.catalogs = []
    if request.vars.graph_submit and isinstance(session.catalogs, str):
        session.catalogs = [request.vars.catalogs]
    if isinstance(session.catalogs, str):
        try:
            session.catalogs = session.catalogs.split(",")
        except AttributeError:
            session.catalogs = []
    elif session.catalogs is None:
        session.catalogs = []

    # set the packaged settings values
    settings = get_settings()
    # paras the axis make iterables that are in the form of the final returned data product
    axes = ['xaxis']
    if settings['mode'] != 'hist':
        axes.append('yaxis')
        if 'zaxis' in settings.keys() and settings['zaxis'] != 'none':
            axes.append('zaxis')
    # set the API request for the data values
    url_values = urllib.parse.urlencode(settings)
    full_url = f'{BASE_API_URL}graph/?{url_values}'
    graph_data_web = urllib.request.urlopen(full_url)
    graph_data = json.loads(graph_data_web.read().decode(graph_data_web.info().get_content_charset('utf-8')))

    if settings['mode'] == 'scatter':
        outputs = graph_data['outputs']
        labels = graph_data['labels']
        star_count = graph_data['star_count']
        planet_count = graph_data['planet_count']
        is_loggable = graph_data['is_loggable']
        if planet_count is not None:
            status = f'{planet_count} planets selected from {star_count} stars'
        else:
            status = f'{star_count} stars selected'
        # if there is no data, then return a message
        if not outputs:
            return "No data points to display"
        # handle tooltips
        source = ColumnDataSource(outputs)
        tooltips = "<b>@name</b><br/><div style='max-width:300px'>" + ", ".join(
            [labels[axis] + " = @" + axis + "{0.00}" for axis in set(labels)]) + "</div>"
        hover = HoverTool(tooltips=tooltips)
        # build the bounds
        x_min = min(outputs['xaxis'])
        x_max = max(outputs['xaxis'])
        if x_min == x_max:
            x_min -= 1
            x_max += 1
        y_min = min(outputs['yaxis'])
        y_max = max(outputs['yaxis'])
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
        if settings['xaxislog'] and is_loggable['xaxis']:
            x_axis_type = 'log'
            x_array = np.array(outputs['xaxis'])
            x_range[0] = np.min(x_array[x_array > 0])
        else:
            x_axis_type = 'linear'
        if settings['yaxislog'] and is_loggable['yaxis']:
            y_axis_type = 'log'
            y_array = np.array(outputs['yaxis'])
            y_range[0] = np.min(y_array[y_array > 0])
        else:
            y_axis_type = 'linear'
        # invert the axis if necessary
        if settings['xaxisinv']:
            x_range = x_range[::-1]
        if settings['yaxisinv']:
            y_range = y_range[::-1]
        # build the figure
        p = figure(tools=[TOOLS, hover], width=750, height=625,
                   x_range=x_range,
                   y_range=y_range,
                   x_axis_type=x_axis_type, y_axis_type=y_axis_type)
        p.title.text = status
        p.title.align = 'center'

        # color if needed
        if settings['zaxis1'] != 'none':
            palette = Viridis256
            # invert the z-axis if necessary
            if settings['zaxisinv']:
                palette = palette[::-1]
            # set up a log scale if necessary
            if settings['zaxislog'] and is_loggable['zaxis']:
                mapper = LogColorMapper(palette=palette, low=min(outputs['zaxis']), high=max(outputs['zaxis']))
            else:
                mapper = LinearColorMapper(palette=palette, low=min(outputs['zaxis']), high=max(outputs['zaxis']))
            # build the scatter plot
            p.scatter('xaxis', 'yaxis', fill_color={'field': 'zaxis', 'transform': mapper},
                      line_color={'field': 'zaxis', 'transform': mapper},
                      fill_alpha=0.3, line_alpha=0.8, source=source, size=8)
            color_bar = ColorBar(color_mapper=mapper, height=100, title=labels['zaxis'].replace('_', ' '), border_line_width=1,
                                 border_line_color='#cccccc', label_standoff=7)
            p.add_layout(color_bar)
        else:
            # build the scatter plot
            p.scatter('xaxis', 'yaxis', fill_color='#4E11B7', line_color='#4E11B7', fill_alpha=0.3, line_alpha=0.6,
                      source=source, size=8)

        # callback
        callback = CustomJS(args={'allPlotData': source}, code="""
                const inds = cb_obj.indices;
                const d1 = allPlotData.data;
                const result = inds.map(i => d1['name'][i].replace("HIP ",""));
                $("#star_list").val(result.join(","));
                $("select[name='star_action']").val("only");
                $("select[name='star_source']").val("hip")
            """)
        source.selected.js_on_change('indices', callback)

        # citation
        citation = Label(x=10, y=10, x_units='screen', y_units='screen',
                         text='Hypatia Catalog ' + datetime.now().strftime("%Y-%m-%d"),
                         text_alpha=0.5)
        p.add_layout(citation)

    else:
        # histogram - compare all data to the stars with planets
        hist_all = graph_data['hist_all']
        hist_planet = graph_data['hist_planet']
        edges = graph_data['edges']
        labels = graph_data['labels']
        x_data = graph_data['x_data']
        if not x_data:
            return "No data points to display"
        max_hist_all = float(max(hist_all))
        # normalize if necessary
        if settings['normalize']:
            labels['yaxis'] = "Relative Frequency"
            fill_alpha = 0.5
            line_alpha = 0.2
        else:
            labels['yaxis'] = 'Number of Stellar Systems'
            fill_alpha = 1
            line_alpha = 1
        # set the bounds of the plot
        x_min = min(x_data)
        x_max = max(x_data)
        x_range = [x_min, x_max]
        # invert the plot if necessary
        if settings['xaxisinv']:
            x_range = x_range[::-1]
        # build the plot object
        p = figure(tools=[TOOLS], width=750, height=625,
                   x_range=x_range,
                   y_range=[0, max_hist_all * 1.20])
        p.quad(top=hist_all, bottom=0, left=edges[:-1], right=edges[1:],
               fill_color="maroon", line_color="black", fill_alpha=fill_alpha, line_alpha=line_alpha,
               legend_label="All Hypatia")
        p.quad(top=hist_planet, bottom=0, left=edges[:-1], right=edges[1:],
               fill_color="orange", line_color="black", fill_alpha=fill_alpha, line_alpha=line_alpha,
               legend_label="Exo-Hosts")
        # citation
        citation = Label(x=10, y=10, x_units='screen', y_units='screen',
                         text='Hypatia Catalog ' + datetime.now().strftime("%Y-%m-%d"),
                         text_alpha=0.5)
        p.add_layout(citation)

    if not settings['gridlines']:
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

    # miscellaneous settings
    p.xaxis.axis_label = labels['xaxis'].replace('_', ' ')
    p.yaxis.axis_label = labels['yaxis'].replace('_', ' ')
    p.xaxis.axis_label_text_font_size = "12pt"
    p.xaxis.axis_label_text_font_style = "normal"
    p.xaxis.major_label_text_font_size = "12pt"
    p.xaxis.major_label_text_font_style = "normal"
    p.yaxis.axis_label_text_font_size = "12pt"
    p.yaxis.axis_label_text_font_style = "normal"
    p.yaxis.major_label_text_font_size = "12pt"
    p.yaxis.major_label_text_font_style = "normal"

    # generate PNG, SVG
    if request.extension == "png":
        return export_png(p)
    elif request.extension == "svg":
        p.output_backend = "svg"
        return export_svgs(p)

    # generate HTML
    script, div = components(p)

    # send back to the browser
    return dict(script=script, div=div)


def table():
    # set new session values from the request
    all_request_vars = set(request.vars.keys())
    for key in all_request_vars:
        session[key] = request.vars[key]
    # special parsing for lists as strings
    if request.vars.graph_submit and isinstance(session.catalogs, str):
        session.catalogs = [request.vars.catalogs]
    if isinstance(session.catalogs, str):
        try:
            session.catalogs = session.catalogs.split(",")
        except AttributeError:
            session.catalogs = []
    if isinstance(session.tablecols, str):
        table_columns_set = set(session.tablecols.split(','))
    else:
        table_columns_set = set(session.tablecols)
    show_error = 'spread' in table_columns_set
    for_download = bool(request.vars.download)

    # build the columns
    columns = []
    requested_name_types = []
    requested_stellar_params = []
    requested_planet_params = []
    requested_elements = []

    is_planet = 'planet' in table_columns_set

    # add star name parameters
    if 'names' in table_columns_set:
        columns.extend(TABLE_NAMES)
        requested_name_types = TABLE_NAMES
    else:
        columns.append('star_id')
        requested_name_types.append('star_id')
    if is_planet:
        columns.insert(1, 'nea_name')
        requested_planet_params = TABLE_PLANET + ['nea_name']

    # the elements
    elements_to_use = set()
    if 'Fe' in table_columns_set:
        columns.append('Fe')
        requested_elements.append('Fe')
        elements_to_use.add('Fe')
        if show_error:
            columns.append('Fe_err')
        if 'FeII' in table_columns_set:
            columns.append('FeII')
            requested_elements.append('FeII')
            elements_to_use.add('FeII')
            if show_error:
                columns.append('FeII_err')
    for item in table_columns_set:
        if item[0].isupper() and item not in elements_to_use:
            columns.append(item)
            requested_elements.append(item)
            if show_error:
                columns.append(f'{item}_err')

    # add planet parameters
    if 'planet' in table_columns_set:
        if show_error:
            for planet_param in TABLE_PLANET:
                if planet_param in {'planet_letter', 'nea_name'}:
                    columns.append(planet_param)
                else:
                    columns.append(planet_param)
                    columns.append(f'{planet_param}_err')
        else:
            columns.extend(TABLE_PLANET)
        requested_planet_params = TABLE_PLANET[:]

    # add stellar parameters
    if 'stellar' in table_columns_set:
        if show_error:
            for stellar_param in TABLE_STELLAR:
                columns.append(stellar_param)
                if stellar_param not in {'disk', 'sptype'}:
                    columns.append(f'{stellar_param}_err')
        else:
            columns.extend(TABLE_STELLAR)
        requested_stellar_params = TABLE_STELLAR[:]

    # package all the query parameters
    table_settings = get_settings()
    table_settings['show_error'] = show_error
    table_settings['requested_name_types'] = ';'.join(requested_name_types)
    table_settings['requested_stellar_params'] = ';'.join(requested_stellar_params)
    table_settings['requested_planet_params'] = ';'.join(requested_planet_params)
    table_settings['requested_elements'] = ';'.join(requested_elements)

    # table sorting options
    if request.vars.sort:
        if session.orderby == request.vars.sort:
            session.reverse = not session.reverse
        else:
            session.reverse = False
        session.orderby = request.vars.sort
        table_settings['reverse'] = session.reverse
        table_settings['sort'] = session.orderby
    else:
        table_settings['sort'] = None
        table_settings['reverse'] = False
    # toggle the hover text with this variable
    table_settings['show_hover'] = True  # label this button as "Hover References"

    # request the table data from the API
    table_url_values = urllib.parse.urlencode(table_settings)
    table_full_url = f'{BASE_API_URL}table/?{table_url_values}'
    table_data_web = urllib.request.urlopen(table_full_url)
    table_data = json.loads(table_data_web.read().decode(table_data_web.info().get_content_charset('utf-8')))
    table_dict = table_data['body']
    star_count = table_data['star_count']
    planet_count = table_data['planet_count']
    hover_data = table_data['hover_data']
    if planet_count and 'nea_name' not in columns:
        columns.insert(1, 'nea_name')
    # add the JS wrapper to get element details
    requested_elements_set = set(requested_elements)
    formatted_table = []
    if table_dict:
        for row_index, data_row in list(enumerate(zip(*[table_dict[col_name] for col_name in columns]))):
            formatted_row = []
            for col_name, cell_value in zip(columns, data_row):
                if cell_value == 0.0:
                    cell_value += 0.0
                cell_value_str = f'{cell_value:1.2f}' if isinstance(cell_value, float) else cell_value
                if col_name in requested_elements_set:
                    if cell_value_str != '' and col_name in hover_data.keys():
                        cell_hover_data = hover_data[col_name][row_index]
                        if cell_hover_data:
                            hover_strings = []
                            for key, value in cell_hover_data.items():
                                if value == 0.0:
                                    value += 0.0
                                hover_strings.append(f"{'' if value < 0.0 else ' '}{float(value):1.2f}: {CATALOG_AUTHORS[key]}")
                            cell_value_str = table_cell(
                                value=cell_value_str,
                                hover_text='\n'.join(hover_strings),
                                do_wrapper=not for_download)
                formatted_row.append(cell_value_str)
            formatted_table.append(formatted_row)
    # Make the status label that is above the Periodic Table that controls the data table
    if planet_count:
        status = f'{planet_count} planets selected from {star_count} stars'
    else:
        status = f'{star_count} stars selected'
    # if there are more than 150 stars, show the first 1000 and put a link to load more
    more_rows = False
    if len(formatted_table) > 150 and request.extension == "load":
        if request.vars.showrows:
            rows_to_show = int(request.vars.showrows)
        else:
            rows_to_show = 100
        if len(formatted_table) > rows_to_show:
            formatted_table = formatted_table[:rows_to_show]
            more_rows = True

    return dict(table=formatted_table, status=status, columns=columns, moreRows=more_rows)
