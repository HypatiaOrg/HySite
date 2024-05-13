import time

import numpy as np

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad as AQSimbad
from astroquery.exceptions import TableParseError


simbad_count = 0
count_per_big_sleep = 100
big_sleep_seconds = 30
small_sleep_seconds = 1


def simbad_coord_to_deg(ra: str, dec: str) -> tuple[float, float, str]:
    *_, hms = str(ra).split('\n')
    *_, dms = str(dec).split('\n')
    c = SkyCoord(hms + " " + dms, unit=(u.hourangle, u.deg))
    return c.ra.deg, c.dec.deg, c.to_string('hmsdms')


def count_wrapper(func):
    def wrapper(simbad_name: str):
        global simbad_count
        simbad_count += 1
        print(f"{simbad_name:16} Simbad Query Count: {simbad_count}")
        results = func(simbad_name)
        if count_per_big_sleep <= simbad_count:
            print(f"\nSimbad Query Count: {simbad_count}\n")
            print(f"Sleeping for {big_sleep_seconds} seconds...\n")
            simbad_count = 0
            time.sleep(big_sleep_seconds)
        else:
            print(f"Simbad Query Count: {simbad_count}\n")
            print(f"Sleeping for {small_sleep_seconds} second...\n")
            time.sleep(small_sleep_seconds)
        return results
    return wrapper


@count_wrapper
def query_simbad_star_names(simbad_name: str) -> list[str] or None:
    raw_results = AQSimbad.query_objectids(simbad_name)
    if raw_results is None:
        print(f"  No star name results for {simbad_name} ")
        return None
    else:
        print(f"  Found star name results for {simbad_name} ")
        # we are expecting a table with a single column of star names
        names_list = list(raw_results.columns["ID"])
    return names_list


@count_wrapper
def query_simbad_star_data(simbad_name: str) -> dict or None:
    """
    This is the primary query type for Simbad, it gives the star's Main Simbad ID,
    and it's coordinates.

    :param simbad_name: str - a string that will match a Simbad record.
    :return: list of dicts for multiple objects or a dictionary object with the query data
             for a single query.
    """
    try:
        global simbad_count
        simbad_count += 1
        results_table = AQSimbad.query_object(simbad_name)
    except TableParseError:
        print(f'  SIMBAD Query Exception for {simbad_name}\n')
        return None
    if results_table is None:
        print(f"  No star data results for {simbad_name} ")
        return None
    print(f"  Found star data results for {simbad_name} ")
    return dict(results_table)


def parse_star_data(results_dict: dict) -> dict or list[dict]:
    data_len = len(np.array(results_dict['MAIN_ID']))
    if data_len != 1:
        raise ValueError(f"Expected a single star, found {data_len}, see the results_dict: {results_dict}")
    else:
        data_this_object = {results_key: np.array(results_array_value)[0]
                            for results_key, results_array_value in results_dict.items()}
        ra_deg, dec_deg, hmsdms = simbad_coord_to_deg(data_this_object["RA"], data_this_object["DEC"])
        data_this_object["ra"] = ra_deg
        data_this_object["dec"] = dec_deg
        data_this_object["hmsdms"] = hmsdms
        return data_this_object


def query_simbad_star(test_simbad_name: str) -> tuple[bool, str, list[str], dict[str, any]]:
    star_names = query_simbad_star_names(test_simbad_name)
    if star_names is None:
        return False, '', [], {}
    else:
        star_data = query_simbad_star_data(test_simbad_name)
        parsed_data = parse_star_data(star_data)
        simbad_main_id = parsed_data['MAIN_ID']
        if star_data is None:
            return False, '', star_names, {}
        else:
            return True, simbad_main_id, star_names, parsed_data


if __name__ == "__main__":
    simbad_like_name = "WOLF 359"
    has_simbad_name_test, simbad_main_id_test, star_names_test, star_data_test = query_simbad_star(simbad_like_name)
