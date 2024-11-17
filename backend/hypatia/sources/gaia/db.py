import time

from hypatia.collect import BaseCollection

additional_gaia_params = ['name','dec_epochJ2000','dec_epochJ2000_error','ra_epochJ2000','ra_epochJ2000_error']
astro_query_dr1_params = ['ra', 'ra_error', 'dec', 'dec_error', 'ref_epoch', 'source_id', 'parallax', 'parallax_error',
                          'pmra', 'pmra_error', 'pmdec', 'pmdec_error', 'duplicated_source',
                          'phot_g_mean_flux', 'phot_g_mean_flux_error', 'phot_g_mean_mag']
astro_query_dr2_params = ['ra', 'ra_error', 'dec', 'dec_error', 'ref_epoch', 'source_id',
                          'parallax', 'parallax_error',
                          'pmra', 'pmra_error', 'pmdec', 'pmdec_error', 'duplicated_source',
                          'phot_g_mean_flux', 'phot_g_mean_flux_error',
                          'phot_g_mean_mag',
                          'radial_velocity', 'radial_velocity_error',
                          'teff_val', 'teff_percentile_lower', 'teff_percentile_upper',
                          'r_est', 'r_lo', 'r_hi']
astro_query_dr3_params = ['ra', 'ra_error', 'dec', 'dec_error', 'ref_epoch', 'source_id',
                          'parallax', 'parallax_error',
                          'pmra', 'pmra_error', 'pmdec', 'pmdec_error', 'duplicated_source',
                          'phot_g_mean_flux', 'phot_g_mean_flux_error',
                          'phot_g_mean_mag',
                          'radial_velocity', 'radial_velocity_error',
                          'teff_gspphot', 'teff_gspphot_lower', 'teff_gspphot_upper',
                          'distance_gspphot', 'distance_gspphot_lower', 'distance_gspphot_upper',]
param_to_units = {'ra_epochJ2000': 'deg', 'ra_error': 'deg', 'dec_epochJ2000': 'deg', 'dec_error': 'deg',
                  'ref_epoch': 'Julian Years', 'parallax': 'mas', 'parallax_error': 'mas',
                  'pmra': 'mas/yr', 'pmra_error': 'mas/yr',
                  'pmdec': 'mas/yr', 'pmdec_error': 'mas/yr',
                  'phot_g_mean_flux': 'e-/s', 'phot_g_mean_mag': 'mag',
                  'radial_velocity': 'km/s',
                  'teff_val': 'K', 'teff_percentile_lower': 'K', 'teff_percentile_upper': 'K',
                  'teff_gspphot': 'K', 'teff_gspphot_lower': 'K', 'teff_gspphot_upper': 'K',
                  'r_est': '[pc]', 'r_lo': '[pc]', 'r_hi': '[pc]', 'dist': '[pc]',
                  'distance_gspphot': '[pc]', 'distance_gspphot_lower': '[pc]', 'distance_gspphot_upper': '[pc]',}
string_types = {'name'}
bool_types  = {'duplicated_source'}
int_types = {'source_id'}


def data_type_dict(param_name: str):
    if param_name in string_types:
        return {
            'bsonType': 'string',
            'description': 'must be a string and is not required'
        }
    elif param_name in bool_types:
        return {
            'bsonType': 'bool',
            'description': 'must be a boolean and is not required'
        }
    elif param_name in int_types:
        return {
            'bsonType': 'int',
            'description': 'must be an integer and is not required'
        }
    else:
        return {
            'bsonType': 'double',
            'description': f'must be a double precision float and is not required'
        }


def data_format(param_name: str, param_value: any) -> float | bool | int | str:
    if param_name in string_types:
        return str(param_value)
    elif param_name in bool_types:
        return bool(param_value)
    elif param_name in int_types:
        return int(param_value)
    else:
        try:
            return float(param_value)
        except ValueError:
            raise ValueError(f'Could not convert the value {param_value} to a float for the parameter {param_name}.')

validators = {}
query_params = {}
for dr_num, astro_query_params in [(1, astro_query_dr1_params),
                                   (2, astro_query_dr2_params),
                                   (3, astro_query_dr3_params)]:
    validators[dr_num] = {
        '$jsonSchema': {
            'bsonType': 'object',
            'title': f'The validator schema for the Gaia Data Release {dr_num}',
            'required': ['_id', 'timestamp'],
            'additionalProperties': False,
            'properties': {
                '_id': {
                    'bsonType': 'string',
                    'description': 'must be a string and is required and unique'
                },
                'timestamp': {
                    'bsonType': 'double',
                    'description': 'must be a double and is required'
                },
                'data': {param: data_type_dict(param) for param in additional_gaia_params + astro_query_params},
            }
        }
    }
    query_params[dr_num] = set(astro_query_params)


def parse_gaia_name(gaia_name: str) -> tuple[int, int]:
    gaia_name_lower = gaia_name.lower().strip()
    if not gaia_name_lower.startswith('gaia dr'):
        raise KeyError(f"The given Gaia name is not of the format 'Gaia DR# #', see:{gaia_name}.")
    data_str = gaia_name_lower.replace('gaia dr', '')
    dr_number_str, id_number_str = data_str.split(' ')
    return int(dr_number_str), int(id_number_str)


def string_gaia_name(dr_number: int, id_number: int) -> str:
    return f'Gaia DR{dr_number} {id_number}'


class GaiaRef(BaseCollection):
    def __init__(self, dr_number=2, verbose=False):
        self.verbose = verbose
        super().__init__(collection_name=f'gaiadr{dr_number}', db_name='metadata', verbose=verbose)
        self.dr_number = dr_number
        self.validator = validators[dr_number]
        self.query_params = query_params[dr_number]
        self.gaia_name_type = f'gaia dr{self.dr_number}'
        self.ref_collection = f'gaiadr{self.dr_number}'
        self.local_collection = {gaia_doc['_id']: gaia_doc['data'] for gaia_doc in self.find_all()}
        self.available_ids = set(self.local_collection.keys())

    def add_local_record(self, gaia_data: dict[str, float | bool | int | str]) -> tuple[int, dict[str, float | bool | int | str]]:
        formatted_data = {param_name: data_format(param_name, param_value)
                          for param_name, param_value in gaia_data.items()}
        source_id = formatted_data['source_id']
        if source_id in self.available_ids:
            raise KeyError(f'The Gaia source id {source_id} is already in the database.')
        self.local_collection[source_id] = formatted_data
        self.available_ids.add(source_id)
        return source_id, formatted_data

    def save_record(self, gaia_data: dict[str, float | bool | int | str]):
        source_id, formatted_data = self.add_local_record(gaia_data)
        self.collection.insert_one({'_id': source_id, 'timestamp': time.time(), 'data': formatted_data})

    def save_many_records(self, gaia_records: list[dict[str, float | bool | int | str]]):
        timestamp = time.time()
        self.collection.insert_many([{'_id': source_id, 'timestamp': timestamp, 'data': formatted_data}
                                     for source_id, formatted_data in  [self.add_local_record(gaia_data)
                                                                        for gaia_data in gaia_records]])

    def find(self, gaia_star_id: int):
        if gaia_star_id in self.available_ids:
            return self.local_collection[gaia_star_id]
        return None