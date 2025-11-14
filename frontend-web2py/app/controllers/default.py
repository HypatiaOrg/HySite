import json
import logging
import urllib.request


logging.basicConfig(filename='logging.log', level=logging.DEBUG)
# logging.warning('Test')


# -*- coding: utf-8 -*-
### required - do no delete
def user():
    return dict(form=auth())


def download():
    return response.download(request, db)


def call():
    return service()


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


def init_session(is_targets: bool = False):
    # add default values for missing session variables
    for var_name, default_val in session_defaults_launch.items():
        session_value = session.__getattr__(var_name)
        if session_value is None:
            session[var_name] = default_val
    session['toggle_vars_to_load'] = {key for key in toggle_graph_vars if session[key]}
    # splitting of strings into lists
    if isinstance(session.tablecols, str):
        session.tablecols = session.tablecols.split(',')
    # function argumnents
    session['is_targets'] = is_targets


def launch():
    init_session()
    return dict()


def targets():
    init_session(is_targets=True)
    return dict()


def density():
    init_session()
    return dict()


def hist():
    init_session()
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

def plot_settings():
    all_request_vars = set(request.vars.keys())
    # set new session values (non-toggles controls) from the request
    for key in all_request_vars - toggle_graph_vars:
        session[key] = request.vars[key]
    # these values are toggled by the act of being requested (http POST), and the toggle action is controlled here
    bool_triggers = (all_request_vars & toggle_graph_vars) | session.get('toggle_vars_to_load', set())
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
            session.catalogs = session.catalogs.split(',')
        except AttributeError:
            session.catalogs = []
    elif session.catalogs is None:
        session.catalogs = []
def scatter_format():
    plot_settings()
    # set the packaged settings values
    settings = get_settings()
    # paras the axis make iterables that are in the form of the final returned data product
    axes = ['xaxis', 'yaxis']
    if 'zaxis' in settings.keys() and settings['zaxis'] != 'none':
        axes.append('zaxis')
    # set the API request for the data values
    url_values = urllib.parse.urlencode(settings)
    full_url = f'{BASE_API_URL}scatter/?{url_values}'
    graph_data_web = urllib.request.urlopen(full_url)
    graph_data = json.loads(graph_data_web.read().decode(graph_data_web.info().get_content_charset('utf-8')))
    # plotting the data based on the settings
    labels = graph_data['labels']

    is_loggable = graph_data['is_loggable']
    do_xlog = settings['xaxislog'] and is_loggable['xaxis']
    do_ylog = settings['yaxislog'] and is_loggable['yaxis']
    do_zlog = settings['zaxislog'] and is_loggable['zaxis']
    has_zaxis = settings['zaxis1'] != 'none'
    outputs = graph_data['outputs']
    return outputs, labels, graph_data, do_xlog, do_ylog, do_zlog, has_zaxis, settings

def graph():
    outputs, labels, graph_data, do_xlog, do_ylog, do_zlog, has_zaxis, settings = scatter_format()
    script, div = create_bokeh_scatter(name=outputs.get('name', []),
                                xaxis=outputs.get('xaxis', []),
                                yaxis=outputs.get('yaxis', []),
                                zaxis=outputs.get('zaxis', []),
                                x_label=labels.get('xaxis', None),
                                y_label=labels.get('yaxis', None),
                                z_label=labels.get('zaxis', None),
                                star_count=graph_data.get('star_count', None),
                                planet_count=graph_data.get('planet_count', None),
                                do_xlog=do_xlog, do_ylog=do_ylog, do_zlog=do_zlog,
                                xaxisinv=settings['xaxisinv'], yaxisinv=settings['yaxisinv'],
                                zaxisinv=settings['zaxisinv'], has_zaxis=has_zaxis,
                                do_gridlines=settings['gridlines'],
                                )
    # send back to the browser
    return dict(script=script, div=div)



def graph_density():
    outputs, labels, graph_data, do_xlog, do_ylog, _do_zlog, _has_zaxis, settings = scatter_format()
    div = create_plotly_hist(name=outputs.get('name', []),
                             xaxis=outputs.get('xaxis', []),
                             yaxis=outputs.get('yaxis', []),
                             x_label=labels.get('xaxis', None),
                             y_label=labels.get('yaxis', None),
                             star_count=graph_data.get('star_count', None),
                             planet_count=graph_data.get('planet_count', None),
                             do_xlog=do_xlog, do_ylog=do_ylog,
                             xaxisinv=settings['xaxisinv'], yaxisinv=settings['yaxisinv'],
                             do_gridlines=settings['gridlines'],
                             show_xyhist=settings['show_xyhist'],
                             xhist_bin_size=settings['xhist_bin_size'],
                             yhist_bin_size= settings['yhist_bin_size'],
                             color_pallet=settings['color_pallet'],
                             )
    # send back to the browser
    return dict(div=div)

def get_requested_handles(settings: dict) -> list[str]:
    requested_handles = []
    if settings['show_has_exo']:
        requested_handles.append('has_exo')
    if settings['show_thin_disk']:
        requested_handles.append('thin_disk')
    if settings['show_thick_disk']:
        requested_handles.append('thick_disk')
    if settings['show_hwo_tier2']:
        requested_handles.append('hwo_tier2')
    if settings['show_hwo_tier1']:
        requested_handles.append('hwo_tier1')
    return requested_handles


def graph_targets():
    plot_settings()
    # set the packaged settings values
    settings = get_settings()
    # set the API request for the data values
    url_values = urllib.parse.urlencode(settings)
    full_url = f'{BASE_API_URL}targets/?{url_values}'
    graph_data_web = urllib.request.urlopen(full_url)
    graph_data = json.loads(graph_data_web.read().decode(graph_data_web.info().get_content_charset('utf-8')))
    # plotting the data based on the settings
    labels = graph_data['labels']
    is_loggable = graph_data['is_loggable']
    do_xlog = settings['xaxislog'] and is_loggable['xaxis']
    do_ylog = settings['yaxislog'] and is_loggable['yaxis']
    outputs = graph_data['outputs']
    script, div = create_bokeh_targets(name=outputs.get('name', []),
                                       xaxis=outputs.get('xaxis', []),
                                       yaxis=outputs.get('yaxis', []),
                                       target_handles=graph_data['targets'],
                                       x_label=labels.get('xaxis', None),
                                       y_label=labels.get('yaxis', None),
                                       do_xlog=do_xlog, do_ylog=do_ylog,
                                       xaxisinv=settings['xaxisinv'], yaxisinv=settings['yaxisinv'],
                                       do_gridlines=settings['gridlines'],
                                       show_all_hypatia=settings['show_all'],
                                       do_or_logic=settings['or_logic'],
                                       requested_handles=get_requested_handles(settings=settings),
                                       )
    return dict(script=script, div=div)


def graph_hist():
    plot_settings()
    # set the packaged settings values
    settings = get_settings()
    # set the API request for the data values
    url_values = urllib.parse.urlencode(settings)
    full_url = f'{BASE_API_URL}hist/?{url_values}'
    graph_data_web = urllib.request.urlopen(full_url)
    graph_data = json.loads(graph_data_web.read().decode(graph_data_web.info().get_content_charset('utf-8')))
    # plotting the data based on the settings
    labels = graph_data['labels']
    script, div = create_bokeh_hist(hist_all=graph_data['hist_all'], hist_planet = graph_data['hist_planet'],
                                    edges=graph_data['edges'],
                                    x_label=labels.get('x_label', None),
                                    x_data = graph_data['x_data'],
                                    normalize=settings['normalize'], xaxisinv=settings['xaxisinv'],
                                    do_gridlines=settings['gridlines'],
                                    )
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
            session.catalogs = session.catalogs.split(',')
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
    fe_elements = set()
    if 'Fe' in table_columns_set:
        columns.append('Fe')
        requested_elements.append('Fe')
        fe_elements.add('Fe')
        if show_error:
            columns.append('Fe_err')
        if 'FeII' in table_columns_set:
            columns.append('FeII')
            requested_elements.append('FeII')
            fe_elements.add('FeII')
            if show_error:
                columns.append('FeII_err')
    other_elements = set()
    for item in table_columns_set:
        if item[0].isupper() and item not in fe_elements:
            other_elements.add(item)
    for element_name in sorted(other_elements, key=element_rank):
        columns.append(element_name)
        requested_elements.append(element_name)
        if show_error:
            columns.append(f'{element_name}_err')

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
    table_settings['show_hover'] = True  # label this button as 'Hover References'

    # is targets table?
    is_targets = session.is_targets
    table_settings['show_targets'] = is_targets

    # request the table data from the API
    table_url_values = urllib.parse.urlencode(table_settings)
    table_full_url = f'{BASE_API_URL}table/?{table_url_values}'
    table_data_web = urllib.request.urlopen(table_full_url)
    table_data = json.loads(table_data_web.read().decode(table_data_web.info().get_content_charset('utf-8')))
    table_dict = table_data['body']
    star_count = table_data['star_count']
    planet_count = table_data['planet_count']
    hover_data = table_data['hover_data']
    if is_targets:
        targets = table_data['targets']
        # if this is a target table, then the targets are in the first column
        columns.insert(1, 'targets')
        table_dict['targets'] = targets
    if planet_count and 'nea_name' not in columns:
        columns.insert(1, 'nea_name')
    settings = get_settings()
    requested_handles = get_requested_handles(settings=settings)
    requested_handles_set = set(requested_handles)
    # add the JS wrapper to get element details
    requested_elements_set = set(requested_elements)
    hover_text_set = set(requested_elements) | set(requested_stellar_params) | set(requested_planet_params)
    formatted_table = []
    if table_dict:
        for row_index, data_row in list(enumerate(zip(*[table_dict[col_name] for col_name in columns]))):
            # Determine if targets are selected, and if so, determine is this row is a target
            if is_targets:
                target_handles = set(targets[row_index])
                if target_handles.isdisjoint(requested_handles_set):
                    continue
            # format the row data
            formatted_row = []
            for col_name, cell_value in zip(columns, data_row):
                if cell_value == 0.0:
                    cell_value += 0.0
                if isinstance(cell_value, str):
                    cell_value_str = cell_value
                elif cell_value is None:
                    cell_value_str = ''
                elif col_name in requested_elements_set:
                    cell_value_str = f'{cell_value:1.2f}'
                elif col_name in COL_FORMAT.keys():
                    cell_value_str = COL_FORMAT[col_name] % cell_value
                elif col_name == 'targets':
                    # if this is a target table, then the targets are in the first column
                    cell_value_str = ', '.join([targets_metadata[target_handle]['title'] for target_handle in cell_value])
                else:
                    cell_value_str = str(cell_value)
                if col_name in hover_text_set:
                    if cell_value_str != '' and col_name in hover_data.keys():
                        cell_hover_data = hover_data[col_name][row_index]
                        if cell_hover_data:
                            if col_name in requested_elements_set:
                                hover_strings = []
                                for key, value in cell_hover_data.items():
                                    if value == 0.0:
                                        value += 0.0
                                    hover_strings.append(f"{'' if value < 0.0 else ' '}{float(value):1.2f}: {CATALOG_AUTHORS[key]}")
                            else:
                                hover_strings = [cell_hover_data]
                            cell_value_str = table_cell(
                                value=cell_value_str,
                                hover_text='\n'.join(hover_strings),
                                do_wrapper=not for_download)
                formatted_row.append(cell_value_str)
            formatted_table.append(formatted_row)
    # Make the status label that is above the Periodic Table that controls the data table
    if planet_count:
        status = f'{len(formatted_table)} planets selected from {star_count} stars'
    else:
        status = f'{len(formatted_table)} stars selected'
    # Only some the default number of rows, and trigger a button that we some all the whole table
    more_rows = False
    if not request.vars.showrows and len(formatted_table) > default_table_rows_to_show:
        formatted_table = formatted_table[:default_table_rows_to_show]
        more_rows = True
    return dict(table=formatted_table, status=status, columns=columns, moreRows=more_rows)
