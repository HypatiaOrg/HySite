import os


"""
Directory paths in the Hypatia Database Pipeline
"""
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
repo_dir = os.path.dirname(base_dir)
projects_dir = os.path.dirname(repo_dir)

working_dir = os.path.join(base_dir, 'hypatia')
configs_dir = os.path.join(working_dir, 'configs')

output_products_dir = os.path.join(base_dir, 'output')
cat_pickles_dir = os.path.join(output_products_dir, 'catalog_pickles')

plot_dir = os.path.join(output_products_dir, 'plots')
xy_plot_dir = os.path.join(plot_dir, 'xy_plot')
histo_dir = os.path.join(plot_dir, 'hist')

star_data_output_dir = os.path.join(output_products_dir, 'star_data_output')
test_database_dir = os.path.join(output_products_dir, 'database_test')


"""
Directory paths for the private access to a HyData repository
"""
hydata_dir = os.path.join(working_dir, 'HyData')
WriteError = False
if os.path.exists(hydata_dir):
    hydata_found = True
else:
    hydata_found = False
    print('The HyData directory is not found, using a local directory.')
    hydata_dir = os.path.join(working_dir, 'local_data')
    if not os.path.exists(hydata_dir):
        print('The local_data directory is not found, creating a new directory.')
        try:
            os.mkdir(hydata_dir)
        except OSError:
            WriteError = True

target_list_dir = os.path.join(hydata_dir, 'target_lists')
ref_dir = os.path.join(hydata_dir, 'reference_data')
abundance_dir = os.path.join(hydata_dir, 'abundance_data')
new_abundances_dir = os.path.join(abundance_dir, 'new_data')
if not hydata_found and not WriteError:
    # create any missing directories need for the HyData directory structure.
    if not os.path.exists(target_list_dir):
        os.mkdir(target_list_dir)
    if not os.path.exists(ref_dir):
        os.mkdir(ref_dir)
    if not os.path.exists(abundance_dir):
        os.mkdir(abundance_dir)
    if not os.path.exists(new_abundances_dir):
        os.mkdir(new_abundances_dir)


"""
File locations
"""
# the environment file
env_filename = os.path.join(repo_dir, '.env')
# the units and parameters file
params_and_units_file = os.path.join(configs_dir, 'params_units.toml')

# source data files in the private HyData repository
xhip_file = os.path.join(ref_dir, "xhip.csv")
pastel_file = os.path.join(ref_dir, "Pastel20.psv")
solar_norm_ref = os.path.join(ref_dir, "solar_norm_ref.csv")
default_catalog_file = os.path.join(ref_dir, 'catalog_file.csv')
new_catalogs_file_name = os.path.join(ref_dir, 'new_catalogs_file.csv')
element_plusminus_error_file = os.path.join(ref_dir, 'element_plusminus_err.toml')

# toggleable intermediate outputs files
pickle_nat = os.path.join(output_products_dir, 'pickle_nat.pkl')
pickle_out = os.path.join(output_products_dir, 'pickle_output_star_data.pkl')


"""
API URLs

For users without direct database access, the API URLs can be used to access the database.
"""
host = 'https://hypatiacatalog.com'
# host = 'http://localhost'  # useful for local testing
api_route = f'{host}/hypatia/api/'
histogram_api_url = f'{api_route}stats/histogram'
summary_api_url = f'{api_route}metadata/solarnorms'
representative_error_url = f'{api_route}metadata/representative_error'
planetary_api_url = f'{api_route}planets'
graph_api_url = f'{api_route}graph'
table_api_url = f'{api_route}web2py/table'
db_summery_url = f'{api_route}db/summary'
# db_full_url needs performance and rate limit testing
# db_full_url = f'{api_route}db/hypatia'