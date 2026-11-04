import json
import urllib.request


def api_json(path: str, settings: dict | None = None, post: bool = False) -> dict:
    """A JSON response from the API's frontend endpoints, with the settings as the query or the form body."""
    url = f'{BASE_API_URL}{path}'
    data = urllib.parse.urlencode(settings).encode() if settings else None
    if data and not post:
        url, data = f'{url}?{data.decode()}', None
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method='POST' if post else 'GET')) as response:
        return json.loads(response.read().decode(response.info().get_content_charset('utf-8')))


# the text pages keep no session state, so they set no session cookie and write no session file
def index():
    session.forget(response)
    return dict(counts=api_json('home/'))


def help():
    session.forget(response)
    # the catalog count in the text, like the home page's numbers
    return dict(counts=api_json('home/'))


def about():
    session.forget(response)
    return dict()


def nea():
    session.forget(response)
    return dict()


def credits():
    session.forget(response)
    return dict()


def api():
    """The API explanation page, at /api (routes.py)."""
    session.forget(response)
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


def density():
    init_session()
    return dict()


def dropdown():
    return dict()


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

# the plot fragments of the four plot pages share one view (plot.load): the figure, the bin size boxes' warnings
# and the id of the page's plot container
PLOT_FRAGMENT_VIEW = 'default/plot.load'


def bin_warnings(bins: dict | None, boxes: list) -> dict:
    """
    The warnings the API put on a page's bins, by bin size box (boxes: BIN_BOXES_XY or BIN_BOXES_HIST,
    models/plot_plotly.py): the "error" rule was asked for a menu choice without an error (Spectral Type, Disk),
    so the API binned by the standard deviation instead and says why (api.web2py.density.BIN_WARNINGS). The
    page shows the text next to the box, which keeps "error", so the rule applies as soon as another parameter
    is chosen.
    """
    bins = bins or {}
    return {box: bins[axis]['warning'] for box, axis in boxes if (bins.get(axis) or {}).get('warning')}


def bin_sizes_used(bins: dict | None, boxes: list) -> dict:
    """
    The bin widths the API changed to fit the plotted range (api.web2py.density.check_bin_size: "adjusted" on
    the bins), by bin size box, as text for the box. The page puts each into its box, and the session keeps
    it, so the box shows the width the histogram has and the next request asks for that width.
    """
    bins = bins or {}
    sizes = {box: f"{bins[axis]['size']:g}" for box, axis in boxes if (bins.get(axis) or {}).get('adjusted')}
    for box, size in sizes.items():
        session[box] = size
    return sizes


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

def axis_args(axes: dict, prefixes: str) -> dict:
    """The keyword arguments the figure functions take for the axes the API decided (api.web2py.plots,
    axes_from_settings): each axis's label, log and inverse, for the axes named by prefixes ('xy', 'xyz')."""
    args = {}
    for prefix in prefixes:
        axis = axes.get(f'{prefix}axis', {})
        args[f'{prefix}_label'] = axis.get('label', None)
        args[f'do_{prefix}log'] = axis.get('log', False)
        args[f'{prefix}axisinv'] = axis.get('inverse', False)
    return args


def graph():
    plot_settings()
    settings = get_settings()
    graph_data = api_json('scatter/', settings)
    warnings = bin_warnings(graph_data.get('bins'), BIN_BOXES_XY)
    sizes = bin_sizes_used(graph_data.get('bins'), BIN_BOXES_XY)
    # the plot: the API decided the labels and the log/inverted axes (api.web2py.plots); Plotly draws (models/plot_plotly.py)
    axes = graph_data['axes']
    outputs = graph_data['outputs']
    div, axis_types = create_plotly_scatter(name=outputs.get('name', []),
                                            xaxis=outputs.get('xaxis', []),
                                            yaxis=outputs.get('yaxis', []),
                                            zaxis=outputs.get('zaxis', []),
                                            star_count=graph_data.get('star_count', None),
                                            planet_count=graph_data.get('planet_count', None),
                                            has_zaxis='zaxis' in axes,
                                            do_gridlines=settings['gridlines'],
                                            bins=graph_data.get('bins'), show_hist=settings['show_scatter_hist'],
                                            **axis_args(axes, 'xyz'))
    log_bin_warnings(warnings, axis_types)
    response.view = PLOT_FRAGMENT_VIEW
    return dict(div=div, warnings=warnings, sizes=sizes, container='graph')


def graph_targets():
    plot_settings()
    settings = get_settings()
    graph_data = api_json('targets/', settings)
    warnings = bin_warnings(graph_data.get('bins'), BIN_BOXES_XY)
    sizes = bin_sizes_used(graph_data.get('bins'), BIN_BOXES_XY)
    # the plot: the API grouped the stars into layers and decided the axes (api.web2py.plots)
    axes = graph_data['axes']
    outputs = graph_data['outputs']
    div, axis_types = create_plotly_targets(xaxis=outputs.get('xaxis', []),
                                            yaxis=outputs.get('yaxis', []),
                                            layers=graph_data['layers'],
                                            number_of_targets=graph_data['number_of_targets'],
                                            do_gridlines=settings['gridlines'],
                                            bins=graph_data.get('bins'), show_hist=settings['show_targets_hist'],
                                            **axis_args(axes, 'xy'))
    log_bin_warnings(warnings, axis_types)
    response.view = PLOT_FRAGMENT_VIEW
    return dict(div=div, warnings=warnings, sizes=sizes, container='graph_targets')


def graph_hist():
    plot_settings()
    settings = get_settings()
    graph_data = api_json('hist/', settings)
    warnings = bin_warnings({'xaxis': graph_data.get('bins')}, BIN_BOXES_HIST)
    sizes = bin_sizes_used({'xaxis': graph_data.get('bins')}, BIN_BOXES_HIST)
    # the plot: the API made the series over shared bins (api.web2py.plots)
    labels = graph_data['labels']   # the API names them by axis: 'xaxis', 'yaxis'
    div = create_plotly_hist(series=graph_data['series'], edges=graph_data['edges'],
                                    x_range=graph_data['x_range'],
                                    x_label=labels.get('xaxis', None),
                                    normalize=settings['normalize'], xaxisinv=settings['xaxisinv'],
                                    do_gridlines=settings['gridlines'],
                                    )
    response.view = PLOT_FRAGMENT_VIEW
    return dict(div=div, warnings=warnings, sizes=sizes, container='hist')


def graph_density():
    plot_settings()
    settings = get_settings()
    graph_data = api_json('density/', settings)
    warnings = bin_warnings(graph_data.get('bins'), BIN_BOXES_XY)
    sizes = bin_sizes_used(graph_data.get('bins'), BIN_BOXES_XY)
    # the plot: the API chose the points, the bins, the colours and the axes (api.web2py.density)
    axes = graph_data['axes']
    outputs = graph_data['outputs']
    bins = graph_data['bins'] or {}
    div = create_plotly_density(xaxis=outputs.get('xaxis', []),
                                yaxis=outputs.get('yaxis', []),
                                x_bins=bins.get('xaxis', None), y_bins=bins.get('yaxis', None),
                                color_scale=graph_data['color_scale'],
                                histogram_color=graph_data['histogram_color'],
                                do_gridlines=settings['gridlines'],
                                show_xyhist=graph_data['show_xyhist'],
                                **axis_args(axes, 'xy'))
    response.view = PLOT_FRAGMENT_VIEW
    return dict(div=div, warnings=warnings, sizes=sizes, container='density')


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
    table_data = api_json('table/', table_settings, post=True)
    # on the page, a cell with hover text (the catalog values behind it) gets the hover wrapper
    formatted_table = []
    for row, row_hover in zip(table_data['rows'], table_data['hover']):
        formatted_table.append([
            table_cell(value=cell, hover_text=cell_hover, do_wrapper=not for_download) if cell_hover else cell
            for cell, cell_hover in zip(row, row_hover)])
    return dict(table=formatted_table, status=table_data['status'], columns=table_data['columns'],
                moreRows=table_data['moreRows'], totalRows=table_data['totalRows'],
                canLoadAll=table_data['canLoadAll'])
