import os
import dotenv

# directory information in the Hypatia Database
star_names_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.dirname(star_names_dir)
repo_dir = os.path.dirname(base_dir)

working_dir = os.path.join(base_dir, "hypatia")
hydata_dir = os.path.join(working_dir, 'HyData')
ref_dir = os.path.join(hydata_dir, "reference_data")
abundance_dir = os.path.join(hydata_dir, 'abundance_data')

output_products_dir = os.path.join(base_dir, "output")
star_data_output_dir = os.path.join(output_products_dir, "star_data_output")
plot_dir = os.path.join(output_products_dir, "plots")
cat_pickles_dir = os.path.join(output_products_dir, "catalog_pickles")
pickle_nat = os.path.join(output_products_dir, "pickle_nat.pkl")
pickle_out = os.path.join(output_products_dir, "pickle_output_star_data.pkl")

# NASA Exoplanet Archive
exoplanet_archive_filename = os.path.join(ref_dir, "nasaexoplanets.csv")
nea_exo_star_name_columns = [
    "hd_name",
    "hip_name",
    'hostname'
]

nea_might_be_zero = [
    "hostname",
    "pl_letter",
    "discoverymethod",
    "pl_pnum",
    "pl_orbeccen",
    "pl_orbincl"
]

nea_unphysical_if_zero_params = [
    "sy_dist",
    "st_mass",
    "st_masserr1",
    "st_masserr2",
    "st_rad",
    "st_raderr1",
    "st_raderr2",
    "pl_radj",
    "pl_radjerr1",
    "pl_radjerr2",
    "pl_bmassj",
    "pl_bmassjerr1",
    "pl_bmassjerr2",
    "pl_orbsmax",
    "pl_orbsmaxerr1",
    "pl_orbsmaxerr2",
    "pl_orbeccenerr1",
    "pl_orbeccenerr2",
    "pl_orbinclerr1",
    "pl_orbinclerr2"
]

nea_requested_data_types_default = [
    "hostname",
    "pl_letter",
    "discoverymethod",
    "pl_orbper",
    "pl_orbpererr1",
    "pl_orbpererr2",
    "pl_orbsmax",
    "pl_orbsmaxerr1",
    "pl_orbsmaxerr2",
    "pl_orbeccen",
    "pl_orbeccenerr1",
    "pl_orbeccenerr2",
    "pl_orbincl",
    "pl_orbinclerr1",
    "pl_orbinclerr2",
    "pl_bmassj",
    "pl_bmassjerr1",
    "pl_bmassjerr2",
    "pl_radj",
    "pl_radjerr1",
    "pl_radjerr2",
    "sy_dist",
    "st_mass",
    "st_masserr1",
    "st_masserr2",
    "st_rad",
    "st_raderr1",
    "st_raderr2",
    "hd_name",
    "hip_name",
]

# hacked stellar parameters, these will override any values from reference data.
hacked = {"Kepler-84": ('dist', 1443.26796)}


"""
Environmental based Configuration
"""

# Load the .env file
env_path = os.path.join(repo_dir, '.env')
if os.path.exists(env_path):
    dotenv.load_dotenv(env_path)

# MongoDB Configuration
MONGO_HOST = os.environ.get("MONGO_HOST", "hypatiacatalog.com")
MONGO_USERNAME = os.environ.get("MONGO_USERNAME", "username")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "password")
connection_string = f'mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:27017'

# Legacy SQLite and HDF5 data directories
hdf5_data_dir = os.path.join(repo_dir, "WebServer", "web2py", "applications", "hypatia", "hypdata")
sqlite_data_dir = os.path.join(repo_dir, "WebServer", "web2py", "applications", "hypatia", "databases")
test_database_dir = os.path.join(output_products_dir, "database_test")
if not os.path.exists(test_database_dir):
    os.makedirs(test_database_dir)
