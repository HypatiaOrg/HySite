import os
import dotenv
from urllib.parse import quote

# star-names database
default_reset_time_seconds = 60 * 60 * 24 * 365.24 * 3  # 3 years
no_simbad_reset_time_seconds = 60 * 60 * 24 * 365.24  # 1 year

# directory information in the Hypatia Database
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
repo_dir = os.path.dirname(base_dir)
projects_dir = os.path.dirname(repo_dir)

working_dir = os.path.join(base_dir, 'hypatia')
hydata_dir = os.path.join(working_dir, 'HyData')
ref_dir = os.path.join(hydata_dir, 'reference_data')
abundance_dir = os.path.join(hydata_dir, 'abundance_data')
site_dir = os.path.join(hydata_dir, 'site_data')

output_products_dir = os.path.join(base_dir, 'output')
star_data_output_dir = os.path.join(output_products_dir, 'star_data_output')
plot_dir = os.path.join(output_products_dir, 'plots')

default_catalog_file = os.path.join(ref_dir, 'catalog_file.csv')
cat_pickles_dir = os.path.join(output_products_dir, 'catalog_pickles')
pickle_nat = os.path.join(output_products_dir, 'pickle_nat.pkl')
pickle_out = os.path.join(output_products_dir, 'pickle_output_star_data.pkl')

# hacked stellar parameters, these will override any values from reference data.
hacked = {
    'Kepler-84': ('dist', 1443.26796, '[pc]', 'Hypatia Override for Kepler-84'),
}
# For these SIMBAD name the API fails to return a few of the values that are available on the main website.
simbad_parameters_hack = {'Gaia DR2 4087838959097352064':
                              {'DEC': '-16 35 27.118803876'},
                          'BD+39 03309':
                              {'RA': '18 03 47.3520267264'},
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

# Legacy SQLite and HDF5 data directories
hdf5_data_dir = os.path.join(projects_dir, 'WebServer', 'web2py', 'applications', 'hypatia', 'hypdata')
sqlite_data_dir = os.path.join(projects_dir, 'WebServer', 'web2py', 'applications', 'hypatia', 'databases')
test_database_dir = os.path.join(output_products_dir, 'database_test')
if not os.path.exists(test_database_dir):
    os.makedirs(test_database_dir)


