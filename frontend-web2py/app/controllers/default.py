import json
import logging
import urllib.request


logging.basicConfig(filename='logging.log', level=logging.DEBUG)
# logging.warning('Test')


# -*- coding: utf-8 -*-
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
    # set new session values (non-toggles controls) from the request; only known settings are kept
    for key in (all_request_vars - toggle_graph_vars) & session_request_vars:
        session[key] = request.vars[key]
    # toggles (checkboxes): a checked box is sent, an unchecked one is not. So a toggle in the request is
    # on, and a toggle that the sending form has (its "toggle_vars" list) but did not send is off. Toggles
    # that are not on that form keep their session value: the scatter page's form must not switch off the
    # targets page's lists or the histogram's normalization (issue #40). A request without "toggle_vars"
    # (the first load of a page's plot, or an older client) changes no toggle except the ones it sends.
    form_toggles = set((request.vars.toggle_vars or '').split(',')) & toggle_graph_vars
    for key in all_request_vars & toggle_graph_vars:
        session[key] = True
    for key in form_toggles - all_request_vars:
        session[key] = False
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

def graph():
    plot_settings()
    # set the packaged settings values
    settings = get_settings()
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
                                       do_gridlines=settings['gridlines'])
    # send back to the browser
    return dict(script=script, div=div)


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
    """The data table page component and its downloads. The table itself is built by the API
    (backend/api/web2py/table.py); this function keeps the session and renders what comes back."""
    # set new session values from the request; only known settings are kept
    all_request_vars = set(request.vars.keys())
    for key in all_request_vars & session_request_vars:
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
        session.tablecols = session.tablecols.split(',')
    for_download = bool(request.vars.download)
    # table sorting: a second click on the same column reverses the order
    if request.vars.sort:
        if session.orderby == request.vars.sort:
            session.reverse = not session.reverse
        else:
            session.reverse = False
        session.orderby = request.vars.sort
    table_settings = get_settings()
    table_settings.update(
        tablecols=','.join(session.tablecols),
        sort=session.orderby if request.vars.sort else None,
        reverse=session.reverse if request.vars.sort else False,
        show_targets=session.is_targets,
        showrows=bool(request.vars.showrows),
        download=for_download,
    )
    # the table from the API; a POST, since a star list can make the settings longer than a URL
    table_request = urllib.request.Request(f'{BASE_API_URL}table/',
                                           data=urllib.parse.urlencode(table_settings).encode(), method='POST')
    table_data_web = urllib.request.urlopen(table_request)
    table_data = json.loads(table_data_web.read().decode(table_data_web.info().get_content_charset('utf-8')))
    # on the page, a cell with hover text (the catalog values behind it) gets the hover wrapper
    formatted_table = []
    for row, row_hover in zip(table_data['rows'], table_data['hover']):
        formatted_table.append([
            table_cell(value=cell, hover_text=cell_hover, do_wrapper=not for_download) if cell_hover else cell
            for cell, cell_hover in zip(row, row_hover)])
    return dict(table=formatted_table, status=table_data['status'], columns=table_data['columns'],
                moreRows=table_data['moreRows'], totalRows=table_data['totalRows'],
                canLoadAll=table_data['canLoadAll'])
