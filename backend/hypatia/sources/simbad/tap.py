from astropy.table import Table
from astroquery.simbad import Simbad

from hypatia.sources.simbad.query import count_wrapper, parse_star_data



def table_to_dict_format(table_data: Table) -> list[dict[str, any]]:
    dict_data = dict(table_data)
    table_columns = list(dict_data.keys())
    return [{column_name: data_value for column_name, data_value in zip(table_columns, data_row)}
            for data_row in zip(*[list(dict_data[key]) for key in table_columns])]


@count_wrapper
def show_table_definitions(table_name: str = 'basic'):
    return table_to_dict_format(Simbad.list_columns(table_name))


@count_wrapper
def get_aliases_by_main_ids(main_ids: set[str]) -> dict[str, list[str]]:
    data_rows = table_to_dict_format(Simbad.query_tap(f"""
        SELECT requested.main_id AS main_id, ids.ids AS ids
        FROM basic
        JOIN TAP_UPLOAD.requested AS requested ON basic.main_id = requested.main_id
        JOIN ids ON basic.oid = ids.oidref;
        """, requested=Table([list(sorted(main_ids))], names=['main_id'])))
    return {row['main_id'].strip(): row['ids'].split('|') for row in data_rows}


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
        SELECT requested.oid AS requested_oid, basic.main_id AS main_id, basic.ra AS "ra", basic.dec AS "dec", 
        basic.sp_type AS sptype, basic.sp_bibcode AS sp_bibcode, ids.ids AS aliases
        FROM basic
        JOIN TAP_UPLOAD.requested AS requested ON basic.oid = requested.oid
        JOIN ids ON basic.oid = ids.oidref;
        """, requested=Table([list(sorted(oids))], names=['oid']))):
        return_rows[row['requested_oid']] = parse_star_data({
            'main_id': row['main_id'] ,
            'ra': row['ra'],
            'dec': row['dec'],
            'sptype': row['sptype'],
            'sp_bibcode': row['sp_bibcode'],
            'aliases': row['aliases'].split('|')
        })
    return return_rows



if __name__ == '__main__':
    # basic_table = show_table_definitions('basic')
    # ids_table = show_table_definitions('ids')
    # ident_table = show_table_definitions('ident')
    #
    main_ids_test = ['BD+44  4548', 'Wolf  418', 'HD 1326']
    # results_dict = get_aliases_by_main_ids(main_ids={main_id.strip() for main_id in main_ids_test})
    # #                          not a main_id but in SIMBAD  , not a real star not in SIMBAD
    test_ids = main_ids_test + ['Gaia DR2 2102468134431912064', 'HD 1467104']
    results = get_from_any_ids(set(test_ids))

