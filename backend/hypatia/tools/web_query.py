import time
import requests
from warnings import warn

from hypatia.configs.file_paths import graph_api_url


def query_hypatia_catalog(url: str,
                          params: dict[str, any] | None = None,
                          verbose: bool = True,
                          show_warnings: bool = False
                          ) -> (dict[str, any] | None, requests.Response):
    start_time = time.time()
    if verbose:
        print(f'Submitting with url: {url}')
        if params is not None:
            print(f'  Parameters: {params}')
    if params is None:
        response = requests.get(url)
    else:
        response = requests.get(url, params=params)
    if response.status_code == 200:
        if verbose:
            print(f'  Query completed successfully.')
        json = response.json()
    else:
        if show_warnings:
            warn(f'Error code: {response.status_code}')
            warn(f'Error text: {response.text}')
        json = None
    if verbose:
        print(f'  Query took {"%2.3f" % (time.time() - start_time)} seconds.')
    return json, response


def get_graph_data(xaxis1: str, xaxis2: str | None = None, yaxis1: str = None, yaxis2: str = None
              )-> dict[str, list[float |str]] | None:
    """
    See more input parameter options at https://hypatiacatalog.com/api under the section `GET data`.
    Or read the code for the function graph_query_from_request() in HySite/backend/api/web2py/data_process.py
    """
    params = {'xaxis1': xaxis1, 'mode': 'scatter'}
    if xaxis2 is not None:
        params['xaxis2'] = xaxis2
    if yaxis1 is not None:
        params['yaxis1'] = yaxis1
    if yaxis2 is not None:
        params['yaxis2'] = yaxis2
    data, _response = query_hypatia_catalog(url=graph_api_url, params=params)
    if data is None:
        return None
    return data