import requests

from hypatia.tools.table_read import num_format


nea_host_name_rank_order = [
    'gaia_id',
    'tic_id',
    "hip_name",
    "hd_name",
    'hostname',
]

nea_host_level_params = {
    "hd_name",
    "hip_name",
    'hostname',
    'tic_id',
    'gaia_id',
    "sy_dist",
    "st_mass",
    "st_rad",
}

nea_unphysical_if_zero_params = {
    "sy_dist",
    "st_mass",
    "st_rad",
    "pl_radj",
    "pl_bmassj",
    "pl_orbsmax",
}

nea_has_error_params = [
    "sy_dist",
    "pl_orbper",
    "pl_orbsmax",
    "pl_orbeccen",
    "pl_orbincl",
    "pl_bmassj",
    "pl_radj",
    "st_mass",
    "st_rad",
]

nea_requested_data_types_default = [
    "hostname",
    "pl_letter",
    "pl_name",
    "hd_name",
    "hip_name",
    "tic_id",
    "gaia_id",
    "discoverymethod",
]
for has_error_param in nea_has_error_params:
    nea_requested_data_types_default.extend([has_error_param, f"{has_error_param}err1", f"{has_error_param}err2"])

nea_has_error_params = set(nea_has_error_params)

items_str = ",".join(nea_requested_data_types_default)
# <https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html>
query_str = f'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+{items_str}+from+ps&format=tsv'


nea_to_hypatia_fields = {
    "hostname": "nea_name",
    "hd_name": "hd",
    "hip_name": "hip",
    "tic_id": "tic",
    "gaia_id": "gaia dr2",
    "sy_dist": "dist",
    "st_mass": "mass",
    "st_rad": "rad",
    "pl_letter": "letter",
    "pl_name": "pl_name",
    "discoverymethod": "discovery_method",
    "pl_orbper": "period",
    "pl_orbsmax": "semi_major_axis",
    "pl_orbeccen": "eccentricity",
    "pl_orbincl": "inclination",
    "pl_bmassj": "pl_mass",
    "pl_radj": "pl_radius",
}

non_parameter_fields = {'_id', 'nea_name', "attr_name", 'hip', 'hd', 'tic', 'gaia dr2',
                        'planet_letters', 'planets', 'letter', 'pl_name'}


hypatia_host_level_params = {nea_to_hypatia_fields[key] for key in nea_host_level_params}
hypatia_host_name_rank_order = [nea_to_hypatia_fields[key] for key in nea_host_name_rank_order]


def format_name_nea_row(row: dict[str, str]) -> dict[str, str | float | int]:
    formatted_row = {}
    remove_keys = []
    for key, value in row.items():
        if value != "":
            if key in nea_unphysical_if_zero_params:
                value_num = num_format(value)
                if value_num == 0:
                    # flag this and the error values to be removed
                    remove_keys.append(key)
                else:
                    formatted_row[key] = num_format(value)
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
        if key.endswith("err1") or key.endswith("err2"):
            prime_key, err_num = key.rsplit("err", 1)
            if err_num == "2":
                inner_key = f'err_low'
            else:
                inner_key = f'err_high'
        elif key in nea_has_error_params:
            prime_key = key
            inner_key = "value"
        else:
            error_grouped[key] = value
            # there is no inner key for this value, so skip to the next key
            continue
        found_error_keys.add(prime_key)
        if prime_key in error_grouped:
            error_grouped[prime_key][inner_key] = value
        else:
            error_grouped[prime_key] = {inner_key: value}
    # format the error values in a consistent way
    for prime_key in found_error_keys:
        value_and_error = error_grouped[prime_key]
        if "value" not in value_and_error.keys():
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
    # rename the filed names to the hypatia standard now the data in a json format
    for key, value in list(error_grouped.items()):
        hypatia_key = nea_to_hypatia_fields[key]
        if hypatia_key != key:
            error_grouped[nea_to_hypatia_fields[key]] = value
            del error_grouped[key]
    return error_grouped


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
