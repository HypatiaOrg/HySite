import time
from urllib.parse import quote_plus
from requests.exceptions import ConnectionError

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad as AQSimbad
from astroquery.exceptions import TableParseError

from hypatia.tools.color_text import simbad_error_text
from hypatia.config import simbad_parameters_hack, simbad_big_sleep_seconds, simbad_small_sleep_seconds


connection_error_max_retries = 5
null_simbad_values = {'', '--'}


def simbad_url(simbad_name: str) -> str:
    url_id = quote_plus(simbad_name).replace(' ', '+')
    return f'https://simbad.cds.unistra.fr/simbad/sim-basic?Ident={url_id}&submit=SIMBAD+search'


def simbad_coord_to_deg(ra: str, dec: str) -> tuple[float, float, str]:
    *_, hms = str(ra).split('\n')
    *_, dms = str(dec).split('\n')
    c = SkyCoord(hms + ' ' + dms, unit=(u.hourangle, u.deg))
    return c.ra.deg, c.dec.deg, c.to_string('hmsdms')


def count_wrapper(func):
    def wrapper(simbad_name: str | list[str] | set[str]):
        start_time = time.time()
        if isinstance(simbad_name, str):
            items_number = 1
            name_str = simbad_name
        else:
            items_number = len(simbad_name)
            name_str = ', '.join([str(one_name) for one_name in simbad_name])
        for connection_error_index in range(connection_error_max_retries + 1):
            print(f'Query for {items_number} item(s): {name_str}')
            try:
                results = func(simbad_name)
            except ConnectionError:
                print(f'  {simbad_error_text("Connection Error")} for:  {name_str}')
                if connection_error_max_retries > connection_error_index:
                    connection_error_number = connection_error_index + 1
                    print(f'  Sleeping for {simbad_big_sleep_seconds:1.3f} seconds then')
                    print(f'  Retrying {connection_error_number} of {connection_error_max_retries}')
                    time.sleep(simbad_big_sleep_seconds)
            else:
                break
        else:
            raise ConnectionError(f'Connection Error for {name_str}, max retries ({connection_error_max_retries}) reached')
        delta_time = time.time() - start_time
        sleep_time = max(simbad_small_sleep_seconds - delta_time, 0.0)
        if sleep_time > 0.0:
            print(f'Sleeping for {sleep_time:1.3} seconds...\n')
            time.sleep(sleep_time)
        return results
    return wrapper


@count_wrapper
def query_simbad_star_names(simbad_name: str) -> list[str] or None:
    raw_results = AQSimbad.query_objectids(simbad_name)
    if raw_results is None:
        print(f'  No star name results for {simbad_name} ')
        return None
    else:
        print(f'  Found star name results for {simbad_name} ')
        # we are expecting a table with a single column of star names
        names_list = list(raw_results.columns['ID'])
    return names_list


@count_wrapper
def query_simbad_star_data(simbad_name: str) -> dict or None:
    """
    This is the primary query type for Simbad, it gives the star's Main Simbad ID,
    and it's coordinates.

    :param simbad_name: str - a string that will match a Simbad record.
    :return: A dictionary object with the query data for a single query.
    """
    try:
        results_table = AQSimbad.query_object(simbad_name)
    except TableParseError:
        print(f'  SIMBAD Query Exception for {simbad_name}\n')
        return None
    if results_table is None:
        print(f'  No star data results for {simbad_name} ')
        return None
    print(f'  Found star data results for {simbad_name} ')
    results_dict = dict(results_table)
    data_len = len(np.array(results_dict['MAIN_ID']))
    if data_len != 1:
        raise ValueError(f'Expected a single star, found {data_len}, see the results_dict: {results_dict}')
    else:
        data_this_object = {results_key: np.array(results_array_value)[0]
                            for results_key, results_array_value in results_dict.items()}
    return data_this_object


def parse_star_data(star_data: dict[str, any]) -> dict[str, any]:
    star_data_lower = {key.lower(): value for key, value in star_data.items() if str(value) not in null_simbad_values}
    main_id = star_data_lower['main_id']
    if 'ra' not in star_data_lower.keys() and 'dec' not in star_data_lower.keys():
        # this is a known issue where RA and Dec values are not available on SIMBAD.
        print(f'    No RA Dec results from the SIMBAD record for {main_id}')
    else:
        ra_raw = star_data_lower['ra']
        dec_raw =star_data_lower['dec']
        if dec_raw == '-':
            print(f'Vist the SIMBAD pages for {main_id} at:')
            print(f'{simbad_url(main_id)}')
            print('This is known issue where the DECLINATION value is not available on the API')
            dec_raw = input('Copy and paste the value here and continue:\n')
        ra_deg, dec_deg, hmsdms = simbad_coord_to_deg(ra=ra_raw, dec=dec_raw)
        star_data_lower['ra'] = ra_deg
        star_data_lower['dec'] = dec_deg
        star_data_lower['hmsdms'] = hmsdms
    return star_data_lower


def query_simbad_star(test_simbad_name: str) -> tuple[str | None, list[str], dict[str, any]]:
    star_names = query_simbad_star_names(test_simbad_name)
    if star_names is None:
        return None, [], {}
    else:
        star_data = query_simbad_star_data(test_simbad_name)
        if test_simbad_name in simbad_parameters_hack.keys():
            replace_values = simbad_parameters_hack[test_simbad_name]
            for key, value in replace_values.items():
                star_data[key] = value
        parsed_data = parse_star_data(star_data)
        simbad_main_id = parsed_data['main_id']
        if star_data is None:
            return None, star_names, {}
        else:
            return simbad_main_id, star_names, parsed_data


if __name__ == '__main__':
    simbad_like_name = 'WOLF 359'
    simbad_main_id_test, star_names_test, star_data_test = query_simbad_star(simbad_like_name)
