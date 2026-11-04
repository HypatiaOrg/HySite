"""
The settings model of the frontend pages: every setting a page can send to the plot and table
endpoints, its default and its kind. One definition, served at /hypatia/api/web2py/settings/, so the
frontend (web2py today, Next.js next) builds its state from it instead of keeping its own copy.

Until October 2026 the defaults and the toggle list lived in the web2py models (summary.py) while the
API parsed the same names in graph_settings_from_request(); this module is the single place for both.
"""
from api.web2py.data_process import (stellar_param_types_v2, planet_param_types_v2, axis_planet_param_types_v2,
                                     plot_norms, available_elements_v2, MAX_FILTERS)
from hypatia.configs.website_settings import (COLOR_PALETTES, DEFAULT_COLOR_PALETTE, BIN_TAGS, BIN_WARNINGS,
                                              LOG_BINS_WARNING, HYPATIA_PURPLE, DEFAULT_X_AXIS, DEFAULT_Y_AXIS,
                                              DEFAULT_SOLARNORM, DEFAULT_STATISTIC, DEFAULT_TABLE_COLUMNS)

# checkboxes: a page sends a toggle only when it is on, and lists its own toggles in "toggle_vars" so
# the server knows which missing ones mean "off" (issue #40)
FILTER_PREFIXES = [f'filter{index}' for index in range(1, MAX_FILTERS + 1)]
TOGGLES = ['normalize', 'gridlines', 'xaxislog', 'yaxislog', 'zaxislog',
           'xaxisinv', 'yaxisinv', 'zaxisinv', *(f'{prefix}_inv' for prefix in FILTER_PREFIXES),
           'show_all', 'or_logic', 'show_hwo_tier1', 'show_hwo_tier2',
           'show_thick_disk', 'show_thin_disk', 'show_has_exo', 'show_xyhist',
           'show_scatter_hist', 'show_targets_hist']

# the state a new session starts with (the keys the pages' forms send, with their first values)
DEFAULTS = {
    # the filters: no parameter, H as the denominator, an open range
    **{f'{prefix}_{part}': value for prefix in FILTER_PREFIXES for part, value in (('1', 'none'), ('2', 'H'), ('3', ''), ('4', ''))},
    'xaxis1': DEFAULT_X_AXIS[0],
    'xaxis2': DEFAULT_X_AXIS[1],
    'yaxis1': DEFAULT_Y_AXIS[0],
    'yaxis2': DEFAULT_Y_AXIS[1],
    'zaxis1': 'none',
    'zaxis2': 'H',
    # the columns the table shows at first (hypatia.configs.website_settings); the table orders them by element
    'tablecols': ','.join(DEFAULT_TABLE_COLUMNS),
    'cat_action': 'exclude',
    'statistic': DEFAULT_STATISTIC,
    'solarnorm': DEFAULT_SOLARNORM,
    'catalogs': [],
    'star_action': 'exclude',
    'star_list': [],
    'show_all': True,
    'show_thin_disk': True,
    'show_thick_disk': True,
    'show_xyhist': True,
    # the scatter and targets pages can show the same histograms along their axes, off to begin with
    'show_scatter_hist': False,
    'show_targets_hist': False,
    # the histograms' bin sizes (a number, or a keyword), shared by the three pages like the axes; the colour palette
    'xhist_bin_size': '',
    'yhist_bin_size': '',
    # the histogram page's bin width, the same rule
    'hist_bin_size': '',
    'color_palette': DEFAULT_COLOR_PALETTE,
}

# other form fields a page may send that the frontend keeps in its session (the table options form)
EXTRA_SESSION_KEYS = ['tablecols', 'tableidentifier', 'tablelist', 'tablesource']

TABLE_TOKENS = ['names', 'names_all', 'planet', 'stellar', 'spread', 'ref']


def settings_schema() -> dict:
    """The settings, their defaults and kinds; the choices where the set is finite."""
    parameters = ['none'] + list(available_elements_v2) + stellar_param_types_v2 + planet_param_types_v2
    axis_parameters = ['none'] + list(available_elements_v2) + stellar_param_types_v2 + axis_planet_param_types_v2
    denominators = ['H'] + list(available_elements_v2)
    fields = {}
    for prefix in FILTER_PREFIXES:
        fields[f'{prefix}_1'] = {'kind': 'choice', 'choices': parameters, 'about': 'the parameter to filter on, or none'}
        fields[f'{prefix}_2'] = {'kind': 'choice', 'choices': denominators, 'about': 'the denominator of an element ratio'}
        fields[f'{prefix}_3'] = {'kind': 'number', 'about': 'the filter minimum, or empty'}
        fields[f'{prefix}_4'] = {'kind': 'number', 'about': 'the filter maximum, or empty'}
        fields[f'{prefix}_inv'] = {'kind': 'toggle', 'about': 'keep the values outside the range instead'}
    for axis in ('xaxis', 'yaxis', 'zaxis'):
        fields[f'{axis}1'] = {'kind': 'choice', 'choices': axis_parameters, 'about': f'the {axis[0]} axis parameter'}
        fields[f'{axis}2'] = {'kind': 'choice', 'choices': denominators, 'about': 'the denominator of an element ratio'}
        fields[f'{axis}log'] = {'kind': 'toggle', 'about': 'logarithmic axis, where the parameter allows it'}
        fields[f'{axis}inv'] = {'kind': 'toggle', 'about': 'inverted axis'}
    fields.update({
        'solarnorm': {'kind': 'choice', 'choices': [norm['id'] for norm in plot_norms], 'about': 'the solar normalization'},
        'statistic': {'kind': 'choice', 'choices': ['median', 'mean'], 'about': 'the value when an element is in several catalogs'},
        'cat_action': {'kind': 'choice', 'choices': ['exclude', 'only'], 'about': 'what the catalogs list does'},
        'catalogs': {'kind': 'list', 'about': 'catalog ids (see the summary)'},
        'star_action': {'kind': 'choice', 'choices': ['exclude', 'only'], 'about': 'what the star list does'},
        'star_list': {'kind': 'list', 'about': 'star names, any SIMBAD name, separated by ;'},
        'normalize': {'kind': 'toggle', 'about': 'histogram: normalize the counts'},
        'gridlines': {'kind': 'toggle', 'about': 'plot gridlines'},
        'show_all': {'kind': 'toggle', 'about': 'targets: show the whole catalog behind the lists'},
        'or_logic': {'kind': 'toggle', 'about': 'targets: a star in any selected list, instead of in all of them'},
        'show_has_exo': {'kind': 'toggle', 'about': 'targets: the exoplanet hosts list'},
        'show_thin_disk': {'kind': 'toggle', 'about': 'targets: the thin disk list'},
        'show_thick_disk': {'kind': 'toggle', 'about': 'targets: the thick disk list'},
        'show_hwo_tier1': {'kind': 'toggle', 'about': 'targets: the HWO tier 1 list'},
        'show_hwo_tier2': {'kind': 'toggle', 'about': 'targets: the HWO tier 2 list'},
        'show_xyhist': {'kind': 'toggle', 'about': 'density: the histograms along the x and y axes'},
        'show_scatter_hist': {'kind': 'toggle', 'about': 'scatter: the histograms along the x and y axes'},
        'show_targets_hist': {'kind': 'toggle', 'about': 'targets: the histograms along the x and y axes, one per list'},
        'xhist_bin_size': {'kind': 'text', 'keywords': BIN_TAGS, 'warnings': BIN_WARNINGS,
                           'about': 'the histograms\' x bin width in data units, or a keyword: the standard '
                                    'deviation of the data (the default) or the representative error of the parameter'},
        'yhist_bin_size': {'kind': 'text', 'keywords': BIN_TAGS, 'warnings': BIN_WARNINGS, 'about': 'the histograms\' y bin width, as for x'},
        'hist_bin_size': {'kind': 'text', 'keywords': BIN_TAGS, 'warnings': BIN_WARNINGS, 'about': 'histogram page: the bin width, as for x'},
        'color_palette': {'kind': 'choice', 'choices': list(COLOR_PALETTES), 'about': 'density: the colour scale'},
        'tablecols': {'kind': 'list', 'choices': TABLE_TOKENS + list(available_elements_v2),
                      'about': 'the table columns: option tokens and element symbols'},
    })
    for name, field in fields.items():
        if name in DEFAULTS:
            field['default'] = DEFAULTS[name]
        elif field['kind'] == 'toggle':
            field['default'] = False
    return dict(defaults=DEFAULTS, toggles=TOGGLES, max_filters=MAX_FILTERS,
                session_keys=sorted(set(DEFAULTS) | set(TOGGLES) | set(EXTRA_SESSION_KEYS)),
                fields=fields,
                # the words and colours the frontend's own drawing needs (hypatia.configs.website_settings)
                words=dict(log_bins_warning=LOG_BINS_WARNING),
                colors=dict(hypatia_purple=HYPATIA_PURPLE))
