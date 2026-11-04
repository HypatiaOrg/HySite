"""
The website's choices, in one place for the science team: what the menus offer and in what order, what the
table shows, the plots' defaults, the histogram and density map rules, and the colours. The code that uses a
choice imports it from here (backend/api/web2py); the frontend reads the ones it needs from the settings
endpoint (/hypatia/api/frontend/settings/), so nothing is typed twice.

What belongs to one parameter (its units, label, decimals, whether it can be logarithmic, its representative
error) is in params_units.toml beside this file, one block per parameter.
"""
from hypatia.object_params import expected_params_dict

# ----- the menus: the stellar and planet parameters a visitor can filter by or put on an axis, in menu order
STELLAR_MENU = ['raj2000', 'decj2000', 'dist', 'x_pos', 'y_pos', 'z_pos', 'teff', 'logg',
                'sptype', 'sptype_num', 'vmag', 'bmag', 'bv', 'pm_ra', 'pm_dec', 'u_vel', 'v_vel', 'w_vel',
                'disk', 'disk_num', 'mass', 'rad']
# the planet letter last (2026-11-02); it is a name, not a number, so it is offered in the filter menus only
PLANET_MENU = ['pl_radius', 'pl_mass', 'period', 'semi_major_axis', 'eccentricity', 'inclination', 'planet_letter']
PLANET_AXIS_MENU = [param for param in PLANET_MENU if param != 'planet_letter']
# the menu choices that are words: the plot shows their ranked number instead
RANKED_STRING_PARAMS = {'sptype': 'sptype_num', 'disk': 'disk_num'}

# ----- the plots' first settings for a new visitor
DEFAULT_X_AXIS = ('Fe', 'H')
DEFAULT_Y_AXIS = ('Si', 'H')
DEFAULT_SOLARNORM = 'lodders09'
DEFAULT_STATISTIC = 'median'

# ----- the data table
# the columns a new visitor sees (2026-11-03); the table orders the elements by atomic number
DEFAULT_TABLE_COLUMNS = ['Fe', 'C', 'O', 'Na', 'Mg', 'Al', 'Si', 'S', 'Ca', 'Sc_II', 'Ti', 'Ni', 'Ba_II', 'Eu_II']
# the name, stellar and planet columns, in the order the table shows them (the planet order of 2026-11-03)
TABLE_NAMES = ['star_id', 'hd', '2mass', 'wds']
TABLE_STELLAR = ['raj2000', 'decj2000', 'x_pos', 'y_pos', 'z_pos', 'dist', 'disk', 'sptype', 'vmag', 'bv',
                 'u_vel', 'v_vel', 'w_vel', 'teff', 'logg', 'mass', 'rad']
TABLE_PLANET = ['planet_letter', 'pl_radius', 'pl_mass', 'period', 'semi_major_axis', 'eccentricity', 'inclination']
# the rows the page shows before "Load All", and the most cells it will show at all (the rest by download)
DEFAULT_TABLE_ROWS_TO_SHOW = 1000
MAX_TABLE_CELLS_TO_SHOW = 250_000

# ----- the histograms (the histogram page, and the ones along the axes of the other plots)
# the keywords a bin size box accepts; the first is what an empty or unreadable box means
BIN_TAGS = ['std dev', 'error']
# the "error" bin width of a stellar or planet parameter: its representative error, in its own units, from the
# parameter's "error" in params_units.toml (elements and ratios take theirs from the catalog summary instead)
PARAMETER_ERRORS = {param: float(fields['error']) for param, fields in expected_params_dict.items() if 'error' in fields}
# what a bin size box says when "error" is asked for a menu choice without one (RANKED_STRING_PARAMS: the plot
# shows the ranked number, which has an error): the number's label from params_units.toml
BIN_WARNINGS = {param: f'Please plot {expected_params_dict[number]["label"]}'
                for param, number in RANKED_STRING_PARAMS.items()}
# what a bin size box says while its axis is logarithmic (Plotly chooses the bins then; 2026-11-02)
LOG_BINS_WARNING = 'Logged bins chosen automatically'
# the most bins an axis gets: a narrower width than the range allows is widened to this many
MAX_BINS = 200
# what a bin size box says when the width it asked for was changed to fit the plotted range: widened to keep to
# MAX_BINS, or cut to the range itself ({size} is the width used, {max_bins} the cap)
BIN_SIZE_WIDENED = 'Bin size widened to {size:g}: at most {max_bins} bins over the plotted range'
BIN_SIZE_CUT = 'Bin size cut to {size:g}, the width of the plotted range'
# the range of the bins: the whole data, a number of standard deviations about the mean, or a manual range
RANGE_MODES = ['full data', 'std dev', 'manual']
DEFAULT_SIGMA = 4.0
# the histogram page's series: a key, its legend label and its colour
HISTOGRAM_SERIES = [('all', 'All Hypatia', 'maroon'), ('exo_hosts', 'Exo-Hosts', 'orange')]

# ----- the colours
HYPATIA_PURPLE = '#4e11b7'
# the density map's colour scales a visitor can choose: Hypatia's own as colour stops, the others by their Plotly
# names; and the colour of the histograms along the map's axes for each scale
COLOR_PALETTES = {
    'HyPurple': [[0.0, HYPATIA_PURPLE], [0.2, '#6c5ce7'], [0.4, '#dfe6e9'], [0.6, '#81ecec'],
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
DEFAULT_HISTOGRAM_COLOR = HYPATIA_PURPLE
