from hypatia.configs.file_paths import graph_api_url
from hypatia.tools.web_query import query_hypatia_catalog


# see more input parameter options at https://hypatiacatalog.com/api under the section `GET data`.
# or read the code for the function graph_query_from_request() in HySite/backend/api/web2py/data_process.py
params = {
    'xaxis1':'Fe',
    'xaxis2':'H',
    'yaxis1':'Si',
    'yaxis2':'H',
    'mode': 'scatter',
}

data, _response = query_hypatia_catalog(url=graph_api_url, params=params)
