import requests

import numpy as np

from hypatia.tools.table_read import num_format

nea_host_name_rank_order = [
    'gaia_dr3_id',
    'gaia_dr2_id',
    'tic_id',
    'hip_name',
    'hd_name',
    'hostname',
]

nea_host_level_params = {
    'hd_name',
    'hip_name',
    'hostname',
    'tic_id',
    'gaia_dr2_id',
    'gaia_dr3_id',
    'sy_dist',
    'st_mass',
    'st_rad',
    'st_teff',
}

nea_unphysical_if_zero_params = {
    'sy_dist',
    'st_mass',
    'st_rad',
    'pl_radj',
    'pl_bmassj',
    'pl_orbsmax',
    'pl_rade',
    'pl_radelim',
    'pl_bmasse',
}

nea_has_error_params = [
    'sy_dist',
    'pl_orbper',
    'pl_orbsmax',
    'pl_orbeccen',
    'pl_orbincl',
    'pl_bmassj',
    'pl_radj',
    'pl_bmasse',
    'pl_rade',
    'st_mass',
    'st_rad',
    'st_teff',
]

nea_requested_data_types_default = [
    'hostname',
    'pl_letter',
    'pl_name',
    'pl_controv_flag',
    'pl_radelim',
    'hd_name',
    'hip_name',
    'tic_id',
    'gaia_dr2_id',
    'gaia_dr3_id',
    'discoverymethod',
]

calculated_params = {
    'radius_gap',
}

bool_params = {
    'pl_controv_flag',
}

a_radius_gap = -0.09
b_radius_gap = 0.21
c_radius_gap = 0.35
def radius_gap_function(period: float, st_mass: float, pl_radius: float) -> float:
    """ Returns positive values. Values above 1 is above the radius gap, likely a mini-Neptune """
    log10_rp = a_radius_gap * np.log10(period) + b_radius_gap * np.log10(st_mass) + c_radius_gap
    return pl_radius / (10.0**log10_rp)


for has_error_param in nea_has_error_params:
    nea_requested_data_types_default.extend([has_error_param, f'{has_error_param}err1', f'{has_error_param}err2'])

nea_has_error_params = set(nea_has_error_params)

items_str = ','.join(nea_requested_data_types_default)
# https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html
query_str = f'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+{items_str}+from+ps&format=tsv'

nea_to_hypatia_fields = {
    'hostname': 'nea_name',
    'hd_name': 'hd',
    'hip_name': 'hip',
    'tic_id': 'tic',
    'gaia_dr2_id': 'gaia dr2',
    'gaia_dr3_id': 'gaia dr3',
    'sy_dist': 'dist',
    'sy_pnum': 'num_planets',
    'st_mass': 'mass',
    'st_rad': 'rad',
    'st_teff': 'teff',
    'pl_letter': 'letter',
    'pl_name': 'pl_name',
    'discoverymethod': 'discovery_method',
    'pl_orbper': 'period',
    'pl_orbsmax': 'semi_major_axis',
    'pl_orbeccen': 'eccentricity',
    'pl_orbincl': 'inclination',
    'pl_bmassj': 'pl_mass',
    'pl_radj': 'pl_radius',
    'pl_radelim': 'pl_radelim',
    'pl_controv_flag': 'pl_controv_flag',
    'pl_bmasse': 'pl_bmasse',
    'pl_rade': 'pl_rade',
}

non_parameter_fields = {
    '_id', 'nea_name', 'attr_name', 'hip', 'hd', 'tic', 'gaia dr2', 'gaia dr3',
    'planet_letters', 'planets', 'letter', 'pl_name', 'pl_radelim',
    *calculated_params,
    *bool_params,
}

hypatia_host_level_params = {nea_to_hypatia_fields[key] for key in nea_host_level_params}
hypatia_host_name_rank_order = [nea_to_hypatia_fields[key] for key in nea_host_name_rank_order]


def calculate_nea_row(row: dict[str, str | float | int]) -> dict[str, str | float | int]:
    if 'period' in row.keys() and 'mass' in row.keys() and 'pl_radius' in row.keys():
        formated_dict = {**row}
        period = float(row['period']['value'])
        mass = float(row['mass']['value'])
        pl_radius = float(row['pl_radius']['value'])
        formated_dict['radius_gap'] = radius_gap_function(period=period, st_mass=mass, pl_radius=pl_radius)
        return formated_dict
    return row


def format_name_nea_row(row: dict[str, str]) -> dict[str, str | float | int]:
    formatted_row = {}
    remove_keys = []
    for key, value in row.items():
        if value != '':
            if key in nea_unphysical_if_zero_params:
                value_num = num_format(value)
                if value_num == 0:
                    # flag this and the error values to be removed
                    remove_keys.append(key)
                else:
                    formatted_row[key] = num_format(value)
            elif key in bool_params:
                formatted_row[key] = value == '1'
            else:
                formatted_row[key] = num_format(value)
    # remove the flagged keys and their error values
    for remove_key in remove_keys:
        for f_key in list(formatted_row.keys()):
            if f_key.startswith(remove_key):
                del formatted_row[f_key]

    # group by primary and error values of the same parameter
    error_grouped = {}
    found_error_keys = set()
    for key, value in list(formatted_row.items()):
        if key.endswith('err1') or key.endswith('err2'):
            prime_key, err_num = key.rsplit('err', 1)
            if err_num == '2':
                inner_key = f'err_low'
            else:
                inner_key = f'err_high'
        elif key in nea_has_error_params:
            prime_key = key
            inner_key = 'value'
        else:
            error_grouped[key] = value
            # there is no inner key for this value, so skip to the next key
            continue
        found_error_keys.add(prime_key)
        if prime_key in error_grouped:
            error_grouped[prime_key][inner_key] = value
        else:
            error_grouped[prime_key] = {inner_key: value}
    # format the error values consistently
    for prime_key in found_error_keys:
        value_and_error = error_grouped[prime_key]
        if 'value' not in value_and_error.keys():
            del error_grouped[prime_key]
        if 'err_low' not in value_and_error.keys() and 'err_high' not in value_and_error.keys():
            continue
        elif 'err_low' not in value_and_error.keys():
            value_and_error['err_low'] = value_and_error['err_high']
        elif 'err_high' not in value_and_error.keys():
            value_and_error['err_high'] = value_and_error['err_low']
        if value_and_error['err_low'] == value_and_error['err_high']:
            value_and_error['err_high'] *= -1
        if 'err_low' in value_and_error.keys() and 'err_high' in value_and_error.keys():
            if value_and_error['err_low'] > value_and_error['err_high']:
                value_and_error['err_low'], value_and_error['err_high'] \
                    = value_and_error['err_high'], value_and_error['err_low']
        # check if the error is zero and delete the error values if it is
        if value_and_error['err_low'] == 0 or value_and_error['err_high'] == 0:
            del value_and_error['err_low']
            del value_and_error['err_high']
    # rename the filed names to the hypatia standard now the data in a json format
    for key, value in list(error_grouped.items()):
        hypatia_key = nea_to_hypatia_fields[key]
        if hypatia_key != key:
            error_grouped[nea_to_hypatia_fields[key]] = value
            del error_grouped[key]
    return calculate_nea_row(error_grouped)


def query_nea() -> list[dict[str, str | float | int]]:
    resp = requests.get(query_str)
    data_rows = resp.text.split('\n')
    header = data_rows[0].split('\t')
    return [format_name_nea_row(dict(zip(header, row.split('\t')))) for row in data_rows[1:] if row]


def set_data_by_host(data: list[dict[str, str | float | int]]) -> dict[str, dict[str, any]]:
    planets_by_host_name = {}
    for nea_star_row in data:
        host_name = nea_star_row['nea_name']
        pl_letter = nea_star_row['letter']
        keys_this_row = set(nea_star_row.keys())
        planet_dict = {key: nea_star_row[key] for key in keys_this_row - hypatia_host_level_params}
        if host_name in planets_by_host_name.keys():
            planets_by_host_name[host_name]['planets'][pl_letter] = planet_dict
        else:
            host_dict = {key: nea_star_row[key] for key in keys_this_row & hypatia_host_level_params}
            host_dict['planets'] = {pl_letter: planet_dict}
            planets_by_host_name[host_name] = host_dict
    return planets_by_host_name


if __name__ == '__main__':
    data = query_nea()
    planets_by_host_name = set_data_by_host(data)
