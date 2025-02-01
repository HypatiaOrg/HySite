import time
import requests
from warnings import warn


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
