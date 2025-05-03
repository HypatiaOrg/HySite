import time
import requests
from warnings import warn

from hypatia.configs.file_paths import graph_api_url, table_api_url


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

def get_table_data(
        show_hover: bool | None = None,
        show_error: bool | None = None,
        requested_name_types: list[str] | None = None,
        requested_stellar_params : list[str] | None = None,
        requested_planet_params: list[str] | None = None,
        requested_elements: list[str] | None = None,
    ) -> dict[str, any] | None:
    table_settings = {}
    if show_hover is not None:
        table_settings['show_hover'] = show_hover
    if show_error is not None:
        table_settings['show_error'] = show_error
    if requested_name_types is not None:
        table_settings['requested_name_types'] = ';'.join(requested_name_types)
    if requested_stellar_params is not None:
        table_settings['requested_stellar_params'] = ';'.join(requested_stellar_params)
    if requested_planet_params is not None:
        table_settings['requested_planet_params'] = ';'.join(requested_planet_params)
    if requested_elements is not None:
        table_settings['requested_elements'] = ';'.join(requested_elements)
    data, _response = query_hypatia_catalog(url=table_api_url, params=table_settings)
    if data is None:
        return None
    return data

if __name__ == '__main__':
    # Example usage
    graph_data = get_graph_data('Teff', 'logg')
    table_data = get_table_data(
        show_error=True,
        show_hover=True,
        requested_name_types=['name', 'HD'],
        requested_stellar_params=['teff', 'logg'],
        requested_planet_params=['pl_mass', 'pl_radius'],
        requested_elements=['Fe', 'O'],
    )
