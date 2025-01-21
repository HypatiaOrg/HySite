import time
from urllib.parse import quote_plus
from requests.exceptions import ConnectionError

from astropy import units as u
from astropy.table import Table
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord

from hypatia.tools.color_text import simbad_error_text
from hypatia.configs.source_settings import simbad_parameters_hack, simbad_big_sleep_seconds, simbad_small_sleep_seconds


connection_error_max_retries = 5
null_simbad_values = {'', '--'}
simbad_last_query_time = 0.0


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
        global simbad_last_query_time
        delta_time = time.time() - simbad_last_query_time
        while delta_time < simbad_small_sleep_seconds:
            sleep_time = simbad_small_sleep_seconds - delta_time + 0.1
            print(f'Sleeping for {sleep_time:1.3} seconds...\n')
            time.sleep(sleep_time)
            delta_time = time.time() - simbad_last_query_time
        if isinstance(simbad_name, str):
            name_str = simbad_name
            print_string = f'Query for one (1) item: {name_str}'
        else:
            items_number = len(simbad_name)
            name_str = ', '.join([str(one_name) for one_name in simbad_name])
            print_string = f'Query for {items_number} item(s): {name_str}'
        for connection_error_index in range(connection_error_max_retries + 1):
            print(print_string)
            simbad_last_query_time = time.time()
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
        return results
    return wrapper


def table_to_dict_format(table_data: Table) -> list[dict[str, any]]:
    dict_data = dict(table_data)
    table_columns = list(dict_data.keys())
    return [{column_name: data_value for column_name, data_value in zip(table_columns, data_row)}
            for data_row in zip(*[list(dict_data[key]) for key in table_columns])]


@count_wrapper
def show_table_definitions(table_name: str = 'basic'):
    return table_to_dict_format(Simbad.list_columns(table_name))


@count_wrapper
def get_from_any_ids(any_ids: set[str]) -> dict[str, dict[str, any]]:
    return_rows = table_to_dict_format(Simbad.query_tap(f"""
        SELECT requested.id AS requested_id, ident.id as id, ident.oidref AS oid
        FROM ident
        JOIN TAP_UPLOAD.requested AS requested ON ident.id = requested.id;
    """, requested=Table([list(sorted(any_ids))], names=['id'])))
    return {row['requested_id'].strip(): {'id': row['id'], 'oid': row['oid']} for row in return_rows}

@count_wrapper
def get_simbad_from_ids(oids: set[str]) -> dict[str, dict[str, any]]:
    return_rows = {}
    for row in table_to_dict_format(Simbad.query_tap(f"""
        SELECT requested.oid AS requested_oid, basic.main_id AS main_id, 
        basic.ra AS "ra", basic.dec AS "dec", basic.coo_bibcode AS "coord_bibcode",
        basic.sp_type AS sptype, basic.sp_bibcode AS sp_bibcode, ids.ids AS aliases
        FROM basic
        JOIN TAP_UPLOAD.requested AS requested ON basic.oid = requested.oid
        JOIN ids ON basic.oid = ids.oidref;
        """, requested=Table([list(sorted(oids))], names=['oid']))):
        main_id = row['main_id']
        # a parameters hack to fix some known issues with the SIMBAD data
        if main_id in simbad_parameters_hack.keys():
            replace_values = simbad_parameters_hack[main_id]
            for key, value in replace_values.items():
                row[key] = value
        # extract parameters
        params = {}
        if ('sptype' in row.keys() and 'sp_bibcode' in row.keys()
                and row['sptype'] not in null_simbad_values and row['sp_bibcode'] not in null_simbad_values):
            params['sptype'] = {'value': row['sptype'], 'ref': f'SIMBAD provided bibcode: {row['sp_bibcode']}'}
        # assemble the data
        data_doc = parse_star_data({
            'main_id': main_id,
            'ra': row['ra'],
            'dec': row['dec'],
            'coord_bibcode': row['coord_bibcode'],
            'aliases': row['aliases'].split('|')
        })
        # check if there are any parameters to add
        if params:
            data_doc['params'] = params
        return_rows[row['requested_oid']] = data_doc
    return return_rows


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
    results_dict = get_from_any_ids({test_simbad_name})
    if results_dict:
        found_oid_id, found_oid_dict = list(results_dict.items())[0]
        found_oid = found_oid_dict['oid']
        return_rows = get_simbad_from_ids({found_oid})
        if return_rows:
            star_data = return_rows[found_oid]
            star_names = star_data['aliases']
            parsed_data = parse_star_data(star_data)
            simbad_main_id = parsed_data['main_id']
            return simbad_main_id, star_names, parsed_data
    return None, [], {}


if __name__ == '__main__':
    simbad_like_name = 'WOLF 359'
    simbad_main_id_test, star_names_test, star_data_test = query_simbad_star(simbad_like_name)
    basic_table = show_table_definitions('basic')
    ids_table = show_table_definitions('ids')
    ident_table = show_table_definitions('ident')
