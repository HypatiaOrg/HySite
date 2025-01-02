import os
from getpass import getuser

import dotenv
from urllib.parse import quote

# User information
current_user = getuser()

# catalog read-in
allowed_name_types = {'Star', 'star', 'Stars', 'starname', 'Starname', 'Name', 'ID', 'Object', 'simbad_id'}

# catalog normalization
norm_keys_default = ['anders89', 'asplund05', 'asplund09', 'grevesse98', 'lodders09', 'original', 'grevesse07']

# star-names database
simbad_big_sleep_seconds = 30.0
simbad_small_sleep_seconds = 1.0
simbad_batch_size = 1000
default_reset_time_seconds = 60 * 60 * 24 * 365.24 * 3  # 3 years
no_simbad_reset_time_seconds = 60 * 60 * 24 * 365.24  # 1 year

# nea database
nea_ref = 'NASA Exoplanet Archive'
known_micro_names = {'kmt', 'ogle', 'moa', 'k2'}
system_designations = {'a', 'b', 'c', 'ab', 'ac', 'bc'}

# directory information in the Hypatia Database
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
repo_dir = os.path.dirname(base_dir)
projects_dir = os.path.dirname(repo_dir)

working_dir = os.path.join(base_dir, 'hypatia')
hydata_dir = os.path.join(working_dir, 'HyData')
ref_dir = os.path.join(hydata_dir, 'reference_data')

abundance_dir = os.path.join(hydata_dir, 'abundance_data')
new_abundances_dir = os.path.join(abundance_dir, 'new_data')
new_catalogs_file_name = os.path.join(ref_dir, 'new_catalogs_file.csv')
default_catalog_file = os.path.join(ref_dir, 'catalog_file.csv')

output_products_dir = os.path.join(base_dir, 'output')
star_data_output_dir = os.path.join(output_products_dir, 'star_data_output')
plot_dir = os.path.join(output_products_dir, 'plots')

cat_pickles_dir = os.path.join(output_products_dir, 'catalog_pickles')
pickle_nat = os.path.join(output_products_dir, 'pickle_nat.pkl')
pickle_out = os.path.join(output_products_dir, 'pickle_output_star_data.pkl')

site_dir = os.path.join(hydata_dir, 'site_data')
params_and_units_file = os.path.join(site_dir, 'params_units.toml')

test_database_dir = os.path.join(projects_dir, 'test_database')

# hacked stellar parameters, these will override any values from reference data.
hacked = {
    'Kepler-84': ('dist', 1443.26796, '[pc]', 'Hypatia Override for Kepler-84'),
}
# For these SIMBAD names, the API fails to return a few of the values that are available on the main website.
simbad_parameters_hack = {'Gaia DR2 4087838959097352064':
                              {'DEC': '-16 35 27.118803876'},
                          'BD+39 03309':
                              {'RA': '18 03 47.3520267264'},
                          }

# NEA provided names that return SIMBAD ids that refer a different part of a multiple star system.
# Example: Gaia DR2 4794830231453653888 is incorrectly associated with HD 41004B in the NEA sources,
# but this GAIA name is for HD 41004A, which also has an entry in the NEA sources.
# one line per star name that is causing the conflict
nea_names_the_cause_wrong_simbad_references = {
    'HD 132563',
    'Gaia DR2 4794830231453653888',
    'TIC 392045047', 'Oph 11',
    'TIC 1129033', # NEA NAME: WASP-77 A
    'HD 358155', 'TIC 442530946', # NEA NAME: WASP-70 A
    'TIC 122298563', 'Kepler-759', # NEA NAME: Kepler-759
    'HIP 14101', # LTT 1445 A
    'TIC 21113347', # HATS-58 A
    'TIC 37348844', 'NGTS-10', # NEA NAME: HATS-58 A
    'Gaia DR2 2106370541711607680', # NEA NAME: Kepler-983
    'TIC 454227159', '2MASS J11011926-7732383', # NEA NAME: 2MASS J11011926-7732383
    'Kepler-1855', # NEA NAME: Kepler-1855
    'TIC 122605766', 'Kepler-497',  # NEA NAME: Kepler-497
    'Kepler-1281', 'TIC 27458799', # NEA NAME: Kepler-1281
    'TIC 171098231', 'Kepler-1309', # NEA NAME: Kepler-1309
    'TIC 120764338', 'Kepler-1495', # NEA NAME: Kepler-1495
    'TIC 239291510', 'Kepler-1802', # NEA NAME: Kepler-1802
    'TIC 26541175', 'Kepler-1437', # NEA NAME: Kepler-1437
    'TIC 63285279', 'Kepler-1534', # NEA NAME: Kepler-1534
}


"""
Environmental based Configuration
"""
none_set = {None, 'none', 'null', ''}

# Load the .env file
env_path = os.path.join(repo_dir, '.env')
if os.path.exists(env_path):
    dotenv.load_dotenv(env_path)

# MongoDB Configuration
MONGO_HOST = os.environ.get('MONGO_HOST', 'hypatiacatalog.com')
MONGO_USERNAME = os.environ.get('MONGO_USERNAME', 'username')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD', 'password')
MONGO_PORT = os.environ.get('MONGO_PORT', '27017')
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', 'test')
MONGO_STARNAMES_COLLECTION = os.environ.get('MONGO_STARNAMES_COLLECTION', 'stars')
INTERACTIVE_STARNAMES = os.environ.get('INTERACTIVE_STARNAMES', 'True').lower() in {'true', '1', 't', 'y', 'yes', 'on'}
CONNECTION_STRING = os.environ.get('CONNECTION_STRING', 'none')
if CONNECTION_STRING.lower() in none_set:
    CONNECTION_STRING = None

def url_encode(string_to_encode: str, url_safe: str = "!~*'()") -> str:
    return quote(string_to_encode.encode('utf-8'), safe=url_safe)

def get_connection_string(user: str = MONGO_USERNAME, password: str = MONGO_PASSWORD,
                          host: str = MONGO_HOST, port: str | int = MONGO_PORT) -> str:
    return f'mongodb://{url_encode(user)}:{url_encode(password)}@{host}:{port}'

if CONNECTION_STRING is None:
    connection_string = get_connection_string()
else:
    connection_string = CONNECTION_STRING

# make directories if they do not exist
if not os.path.exists(output_products_dir):
    os.makedirs(output_products_dir)
test_database_dir = os.path.join(output_products_dir, 'database_test')
if not os.path.exists(test_database_dir):
    os.makedirs(test_database_dir)
