import os
import json
import urllib.parse
import urllib.request


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

COMPOSE_PROFILES = set(os.environ.get('COMPOSE_PROFILES', '').split(','))
if 'api' in COMPOSE_PROFILES:
    BASE_URL_DEFAULT = 'http://localhost'
    BASE_URL = os.environ.get('BASE_API_URL', BASE_URL_DEFAULT)
else:
    BASE_URL = 'https://hypatiacatalog.com'
BASE_API_URL = f'{BASE_URL}/hypatia/api/web2py/'

webURL = urllib.request.urlopen(f'{BASE_API_URL}summary/')
param_data = json.loads(webURL.read().decode(webURL.info().get_content_charset('utf-8')))

units_and_fields = param_data['units_and_fields']
STELLAR_PARAM_TYPES = param_data['stellar_param_types']
PLANET_PARAM_TYPES = param_data['planet_param_types']
ranked_string_params = param_data['ranked_string_params']
CATALOGS = [AttrDict(cat_dict) for cat_dict in param_data['catalogs']]
CATALOG_AUTHORS = {cat['id']: cat['author'] for cat in CATALOGS}
SOLAR_NORMS = [AttrDict(norm_dict) for norm_dict in param_data['solarnorms']]
element_data = param_data['element_data']
representative_error = {element.lower().replace('_', ''): error for element, error in param_data['representative_error'].items()}
h_appended_names = [single_el['element_id'] + 'H' for single_el in element_data]
h_appended_names_set = set(h_appended_names)
rank_ordered_elements = {single_el['element_id']: el_index for el_index, single_el in list(enumerate(element_data))}


def element_rank(element_id: str) -> int:
    """Returns the rank of the element based on its index in the element_data list."""
    return rank_ordered_elements.get(element_id, float('inf'))


COL_FORMAT = {}
COL_PREFERRED_NAME = {}
COL_SHORT_DESC = {}
COL_LONG_DESC = {}
COL_UNITS = {}
for handle, param_defs in units_and_fields.items():
    if 'decimals' in param_defs.keys():
        COL_FORMAT[handle] = f'%.{param_defs["decimals"]}f'
        try:
            exponent= int(f'-{param_defs["decimals"]}')
        except ValueError:
            pass
        else:
            representative_error[handle] = float(f'1.e{exponent + 2}')
    # elif 'units' in param_defs.keys() and param_defs['units'] == 'string':
    else:
        COL_FORMAT[handle] = '%s'
    COL_PREFERRED_NAME[handle] = param_defs['label']
    COL_SHORT_DESC[handle] = param_defs['label']
    COL_LONG_DESC[handle] = param_defs['hover']
    if 'units' in param_defs.keys():
        COL_UNITS[handle] = param_defs['units']
    else:
        COL_UNITS[handle] = ''

COL_PREFERRED_NAME['none'] = 'None'
COL_PREFERRED_NAME['H'] = 'H'
ELEMENT_BUTTON_LABELS = ['H']
for single_el in element_data:
    abv = single_el['abbreviation']
    el_id = single_el['element_id']
    ELEMENT_BUTTON_LABELS.append(abv)
    COL_PREFERRED_NAME[el_id] = abv
    COL_LONG_DESC[el_id] = single_el['element_name']
    COL_SHORT_DESC[el_id] = abv


periodicTable = [
    ['H' ,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,'He'],
    ['Li','Be',None,None,None,None,None,None,None,None,None,None,'B' ,'C' ,'N' ,'O' ,'F' ,'Ne'],
    ['Na','Mg',None,None,None,None,None,None,None,None,None,None,'Al','Si','P' ,'S' ,'Cl','Ar'],
    ['K' ,'Ca','Sc','Ti','V' ,'Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Kr'],
    ['Rb','Sr','Y' ,'Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I' ,'Xe'],
    ['Cs','Ba','Lu','Hf','Ta','W' ,'Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn'],
    ['Fr','Ra','Lr','Rf','Db','Sg','Bh','Hs','Mt','Ds','Rg','Cn','Nh','Fl','Mc','Lv','Ts','Og'],
    [None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None],
    [None,None,'La','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb',None,None],
    [None,None,'Ac','Th','Pa','U' ,'Np','Pu','Am','Cm','Bk','Cf','Es','Fm','Md','No',None,None],
]


name_handles_labels = {'star_id': 'Name', 'hd': 'HD', '2mass': '2MASS', 'wds': 'WDS', 'aliases': 'All Names'}
TABLE_NAMES = [name for name in name_handles_labels.keys()]
name_handles_labels['nea_name'] = 'NEA Name'
name_handles_labels['planet_letter'] = 'Planet Letter'
TABLE_STELLAR = ['raj2000', 'decj2000', 'x_pos', 'y_pos', 'z_pos', 'dist', 'disk', 'sptype', 'vmag', 'bv',
                 'u_vel', 'v_vel', 'w_vel', 'teff', 'logg', 'mass', 'rad']
TABLE_PLANET = ['planet_letter', 'period', 'eccentricity', 'semi_major_axis', 'pl_mass', 'pl_radius', 'inclination']
toggle_graph_vars = {'normalize', 'gridlines', 'show_xyhist', 'xaxislog', 'yaxislog', 'zaxislog',
                     'xaxisinv', 'yaxisinv', 'zaxisinv', 'filter1_inv', 'filter2_inv', 'filter3_inv'}
default_table_rows_to_show = 1000

session_defaults_launch = {
    # must be set in the 'launch' function
    'filter1_1': 'none',
    'filter1_2': 'H',
    'filter2_1': 'none',
    'filter2_2': 'H',
    'filter3_1': 'none',
    'filter3_2': 'H',
    'xaxis1': 'Fe',
    'xaxis2': 'H',
    'yaxis1': 'Si',
    'yaxis2': 'H',
    'zaxis1': 'none',
    'zaxis2': 'H',
    'tablecols': 'Fe,C,O,Mg,Si,S,Ca,Ti',
    # could be set in the 'graph' function, but can also be set in the 'launch' function
    'filter1_3': '',
    'filter1_4': '',
    'filter2_3': '',
    'filter2_4': '',
    'filter3_3': '',
    'filter3_4': '',
    'cat_action': 'exclude',
    'statistic': 'median',
    'solarnorm': 'lodders09',
    'catalogs': [],
    'star_action': 'exclude',
    'star_list': [],
    'xhist_bin_size': None,
    'yhist_bin_size': None,
    'color_pallet': 'hypatia',
}

exported_session_vars = sorted(set(session_defaults_launch.keys()) | toggle_graph_vars)

for name_handle, name_label in name_handles_labels.items():
    COL_PREFERRED_NAME[name_handle] = name_label
    COL_SHORT_DESC[name_handle] = name_label


def is_true_string(value: str) -> bool:
    return value.lower() in {'true', 'yes', '1', 'on', 't', 'y'}


def build_periodic_table(table_id='pt', show_species: bool = False, allow_h: bool = False):
    supported_elements = list(h_appended_names)
    supported_elements_set = set(h_appended_names_set)
    if allow_h:
        hh_str = 'HH'
        supported_elements.append(hh_str)
        supported_elements_set.add(hh_str)
    result = "<table style='margin:0px 10px'>"
    for period in periodicTable:
        result += "<tr style='height:10px'>"
        for element in period:
            result += '<td>'
            if element is not None:
                has_i = element + 'H' in supported_elements_set
                has_ii = element + '_IIH' in supported_elements_set
                if has_i and has_ii and show_species:
                    result += "<nobr><btn title='%(desc)s' class='btn btn-default btn-xs btn-%(table_id)s' id='%(table_id)s-%(element)s' onclick='pick(\"%(table_id)s\",\"%(element)s\")'>%(element)s</btn><btn title='%(desc)s (II)' class='btn btn-default btn-xs btn-%(table_id)s' id='%(table_id)s-%(element)s_II' onclick='pick(\"%(table_id)s\",\"%(element)s_II\")'> II</btn><nobr>" % dict(table_id=table_id,element=element,desc=COL_LONG_DESC.get(element, {}))
                elif has_i or (has_ii and not show_species):
                    result += "<btn title='%(desc)s' class='btn btn-default btn-xs btn-%(table_id)s' id='%(table_id)s-%(element)s' onclick='pick(\"%(table_id)s\",\"%(element)s\")'>%(element)s</btn>" % dict(table_id=table_id,element=element,desc=COL_LONG_DESC.get(element, {}))
                elif has_ii and show_species:
                    result += "<nobr>%(element)s<btn title='%(desc)s' class='btn btn-default btn-xs btn-%(table_id)s' id='%(table_id)s-%(element)s_II' onclick='pick(\"%(table_id)s\",\"%(element)s_II\")'> II</btn></nobr>" % dict(table_id=table_id,element=element,desc=COL_LONG_DESC.get(element + '_II', {}))
                else:
                    result += element
            result += '</td>'
        result += '</tr>'
    result += '</table>'
    return result


table_cell_base = '<b style="cursor:pointer" data-html="true" title="'
table_cell_end = '</b>'


def table_cell(value: float | str | None = None,
               hover_text: str = None,
               do_wrapper: bool = False):
    if do_wrapper and hover_text is not None:
        html_str = f'{table_cell_base}{hover_text}">{value}{table_cell_end}'
        return XML(html_str)
    else:
        return value
