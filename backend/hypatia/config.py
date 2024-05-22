import os
import dotenv

# directory information in the Hypatia Database
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
repo_dir = os.path.dirname(base_dir)
projects_dir = os.path.dirname(repo_dir)

working_dir = os.path.join(base_dir, "hypatia")
hydata_dir = os.path.join(working_dir, 'HyData')
ref_dir = os.path.join(hydata_dir, "reference_data")
abundance_dir = os.path.join(hydata_dir, 'abundance_data')
site_dir = os.path.join(hydata_dir, 'site_data')

output_products_dir = os.path.join(base_dir, "output")
star_data_output_dir = os.path.join(output_products_dir, "star_data_output")
plot_dir = os.path.join(output_products_dir, "plots")
cat_pickles_dir = os.path.join(output_products_dir, "catalog_pickles")
pickle_nat = os.path.join(output_products_dir, "pickle_nat.pkl")
pickle_out = os.path.join(output_products_dir, "pickle_output_star_data.pkl")

# hacked stellar parameters, these will override any values from reference data.
hacked = {
    "Kepler-84": ('dist', 1443.26796, '[pc]', 'Hypatia Override for Kepler-84'),
}


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
hdf5_data_dir = os.path.join(projects_dir, "WebServer", "web2py", "applications", "hypatia", "hypdata")
sqlite_data_dir = os.path.join(projects_dir, "WebServer", "web2py", "applications", "hypatia", "databases")
test_database_dir = os.path.join(output_products_dir, "database_test")
if not os.path.exists(test_database_dir):
    os.makedirs(test_database_dir)


