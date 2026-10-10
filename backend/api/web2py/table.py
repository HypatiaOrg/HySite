"""
The frontend's data table, built in the API: which columns a page's settings ask for, the rows
formatted for display, the hover text behind each cell, the row limits, and the download formats.

Until October 2026 this logic lived in the web2py controller (frontend-web2py/app/controllers/default.py,
table()). It moved here so that any frontend (web2py today, Next.js next) only renders what it gets.
The output is the same, cell for cell, as the web2py version produced.

Request settings (all strings, as a web form sends them):
  the plot settings (filters, axes, solarnorm, statistic, catalogs, star_list, ...) as for the plots;
  tablecols   the table options tokens, comma separated: 'names', 'names_all', 'planet', 'stellar',
              'spread' (error columns), 'ref' (reference columns) and element symbols ('Fe', 'FeII', 'C')
  sort, reverse   the column to sort by and the direction
  show_targets, show_has_exo, show_thin_disk, show_thick_disk, show_hwo_tier1, show_hwo_tier2
              a targets table: only the rows in the selected lists
  showrows    'true' after "Load All": every row, when the table is small enough for a page
  download    'true' for a download: every row, no hover text
  format      'json' (default), 'csv', 'tsv' or 'psv'
"""
from api.v2.data_process import available_catalogs_v2
from api.web2py.data_process import (is_true_str, units_and_fields_v2, targets_metadata, element_data,
                                     table_query_from_request)

# the on-page table shows this many rows, with a "Load All" link for the rest; downloads always get every row
DEFAULT_TABLE_ROWS_TO_SHOW = 1000
# "Load All" is offered only while the whole table (rows x columns, each cell with its hover text) stays
# small enough for a browser; above this, the page points to the downloads instead (issue #43)
MAX_TABLE_CELLS_TO_SHOW = 250_000

TABLE_NAMES = ['star_id', 'hd', '2mass', 'wds']
TABLE_STELLAR = ['raj2000', 'decj2000', 'x_pos', 'y_pos', 'z_pos', 'dist', 'disk', 'sptype', 'vmag', 'bv',
                 'u_vel', 'v_vel', 'w_vel', 'teff', 'logg', 'mass', 'rad']
TABLE_PLANET = ['planet_letter', 'period', 'eccentricity', 'semi_major_axis', 'pl_mass', 'pl_radius', 'inclination']
TARGET_HANDLE_SETTINGS = [('show_has_exo', 'has_exo'), ('show_thin_disk', 'thin_disk'),
                          ('show_thick_disk', 'thick_disk'), ('show_hwo_tier2', 'hwo_tier2'),
                          ('show_hwo_tier1', 'hwo_tier1')]
DOWNLOAD_FORMATS = {'csv': (',', '"'), 'tsv': ('\t', ''), 'psv': ('|', '')}

catalog_authors = {catalog['id']: catalog['author'] for catalog in available_catalogs_v2}
# the column order of the elements: the order of the summary's element list, as the frontend had it
element_order = {element['element_id']: index for index, element in enumerate(element_data)}


def element_rank(element_id: str) -> float:
    return element_order.get(element_id, float('inf'))


# '%.<decimals>f' for the numeric parameters, '%s' for the rest (elements are formatted separately)
column_format = {handle: f"%.{defs['decimals']}f" if 'decimals' in defs else '%s'
                 for handle, defs in units_and_fields_v2.items()}


def split_tokens(value: str | list | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = value.replace(';', ',').split(',')
    return [token.strip() for token in value if token.strip()]


def table_columns(tablecols: set[str]) -> dict:
    """The ordered column list for a set of table option tokens, and the data to request for it."""
    show_error = 'spread' in tablecols
    show_reference = 'ref' in tablecols
    columns = []
    requested_name_types = []
    requested_planet_params = []
    requested_stellar_params = []
    requested_elements = []
    # star names
    if 'names' in tablecols:
        columns.extend(TABLE_NAMES)
        requested_name_types = list(TABLE_NAMES)
    else:
        columns.append('star_id')
        requested_name_types.append('star_id')
    if 'names_all' in tablecols:
        columns.append('aliases')
        requested_name_types.append('aliases')
    if 'planet' in tablecols:
        columns.insert(1, 'nea_name')
    # the elements: Fe (and FeII) first, then the rest in periodic-table rank order
    fe_elements = set()
    if 'Fe' in tablecols:
        columns.append('Fe')
        requested_elements.append('Fe')
        fe_elements.add('Fe')
        if show_error:
            columns.append('Fe_err')
        if show_reference:
            columns.append('Fe_ref')
        if 'FeII' in tablecols:
            columns.append('FeII')
            requested_elements.append('FeII')
            fe_elements.add('FeII')
            if show_error:
                columns.append('FeII_err')
            if show_reference:
                columns.append('FeII_ref')
    other_elements = {item for item in tablecols if item[0].isupper() and item not in fe_elements}
    for element_name in sorted(other_elements, key=element_rank):
        columns.append(element_name)
        requested_elements.append(element_name)
        if show_error:
            columns.append(f'{element_name}_err')
        if show_reference:
            columns.append(f'{element_name}_ref')
    # planet parameters
    if 'planet' in tablecols:
        for planet_param in TABLE_PLANET:
            columns.append(planet_param)
            if planet_param not in {'planet_letter', 'nea_name'}:
                if show_error:
                    columns.append(f'{planet_param}_err')
                if show_reference:
                    columns.append(f'{planet_param}_ref')
        requested_planet_params = list(TABLE_PLANET)
    # stellar parameters
    if 'stellar' in tablecols:
        for stellar_param in TABLE_STELLAR:
            columns.append(stellar_param)
            if stellar_param not in {'disk', 'sptype'}:
                if show_error:
                    columns.append(f'{stellar_param}_err')
                if show_reference:
                    columns.append(f'{stellar_param}_ref')
        requested_stellar_params = list(TABLE_STELLAR)
    return dict(columns=columns, show_error=show_error, show_reference=show_reference,
                requested_name_types=requested_name_types, requested_stellar_params=requested_stellar_params,
                requested_planet_params=requested_planet_params, requested_elements=requested_elements)


def hover_lines(col_name: str, cell_hover_data, is_element: bool, return_median: bool = False) -> list[str]:
    """The lines of hover text behind a cell: the catalog values of an element, or a parameter's reference."""
    if not is_element:
        return [cell_hover_data]
    items = list(cell_hover_data.items())
    if return_median:
        # only the median reference values: the middle one, or the middle two
        count = len(items)
        if count % 2 == 0:
            middle = count // 2
            items = items[middle - 1:middle + 1]
        else:
            middle = (count - 1) // 2
            items = items[middle:middle + 1]
    lines = []
    for key, value in items:
        if value == 0.0:
            value += 0.0
        lines.append(f"{'' if value < 0.0 else ' '}{float(value):1.2f}: {catalog_authors[key]}")
    return lines


def format_cell(col_name: str, value, is_element: bool) -> str | list:
    """A cell as the page shows it; reference and alias cells are lists of lines."""
    if value == 0.0:
        value += 0.0  # -0.0 -> 0.0
    if isinstance(value, str):
        text = value
    elif value is None:
        text = ''
    elif is_element:
        text = f'{value:1.2f}'
    elif col_name in column_format:
        text = column_format[col_name] % value
    elif col_name == 'targets':
        text = ', '.join(targets_metadata[handle]['title'] for handle in value)
    elif col_name.endswith('_ref') or col_name == 'aliases':
        text = value
    else:
        text = str(value)
    if col_name.endswith('_err') and text != '':
        text = f'±{text}'
    return text


def table_from_request(settings) -> dict:
    """The table for a page's settings: columns, formatted rows, hover text per cell, counts and limits."""
    settings = {key: settings.get(key) for key in settings.keys()}
    tablecols = set(split_tokens(settings.get('tablecols')))
    layout = table_columns(tablecols)
    columns = layout['columns']
    show_error, show_reference = layout['show_error'], layout['show_reference']
    for_download = is_true_str(settings.get('download', 'false'))
    is_targets = is_true_str(settings.get('show_targets', 'false'))
    show_all_requested = is_true_str(settings.get('showrows', 'false'))
    # the query: the plot settings as sent, plus what the columns need
    query = dict(settings)
    query.update(
        show_error=str(show_error),
        requested_name_types=';'.join(layout['requested_name_types']),
        requested_stellar_params=';'.join(layout['requested_stellar_params']),
        requested_planet_params=';'.join(layout['requested_planet_params']),
        requested_elements=';'.join(layout['requested_elements']),
        # hover text (the catalog values behind each cell) is shown on the page; a download has no hover,
        # but the reference columns are built from the same data
        show_hover=str((not for_download) or show_reference),
        show_targets=str(is_targets),
    )
    sort = settings.get('sort')
    if sort in (None, '', 'None'):
        query['sort'] = None
        query['reverse'] = 'False'
    table_data = table_query_from_request(settings=query)
    table_dict = table_data['body']
    star_count = table_data['star_count']
    planet_count = table_data['planet_count']
    hover_data = table_data['hover_data']
    targets = table_data.get('targets')
    if is_targets:
        columns.insert(1, 'targets')
        table_dict['targets'] = targets
    if planet_count and 'nea_name' not in columns:
        columns.insert(1, 'nea_name')
    requested_elements_set = set(layout['requested_elements'])
    hover_columns = (requested_elements_set | set(layout['requested_stellar_params'])
                     | set(layout['requested_planet_params']))
    return_median = str(settings.get('statistic', 'median')).lower() == 'median'
    if show_reference:
        for col_name in columns:
            if col_name.endswith('_ref'):
                base_name = col_name.rsplit('_ref', 1)[0]
                hover_this_column = hover_data[base_name]
                table_dict[col_name] = [
                    hover_lines(base_name, cell, base_name in requested_elements_set, return_median=return_median)
                    if cell else '' for cell in hover_this_column]
    rows, hover = [], []
    more_rows = False
    if table_dict:
        row_count = len(table_dict[columns[0]])
        if is_targets:
            # a targets table shows only the stars in the selected lists
            requested_handles = {handle for setting, handle in TARGET_HANDLE_SETTINGS
                                 if is_true_str(settings.get(setting, 'false'))}
            row_indexes = [index for index in range(row_count) if not requested_handles.isdisjoint(targets[index])]
        else:
            row_indexes = list(range(row_count))
        total_rows = len(row_indexes)
        can_load_all = total_rows * len(columns) <= MAX_TABLE_CELLS_TO_SHOW
        show_all_rows = for_download or (show_all_requested and can_load_all)
        if not show_all_rows and total_rows > DEFAULT_TABLE_ROWS_TO_SHOW:
            row_indexes = row_indexes[:DEFAULT_TABLE_ROWS_TO_SHOW]
            more_rows = True
        for row_index in row_indexes:
            row, row_hover = [], []
            for col_name in columns:
                value = table_dict[col_name][row_index]
                is_element = col_name in requested_elements_set
                text = format_cell(col_name, value, is_element)
                cell_hover = None
                if col_name in hover_columns and text != '' and col_name in hover_data:
                    cell_hover_data = hover_data[col_name][row_index]
                    if cell_hover_data:
                        cell_hover = '\n'.join(hover_lines(col_name, cell_hover_data, is_element))
                row.append(text)
                row_hover.append(cell_hover)
            rows.append(row)
            hover.append(row_hover)
    else:
        total_rows = 0
        can_load_all = True
    if planet_count:
        status = f'{total_rows} planets selected from {star_count} stars'
    else:
        status = f'{total_rows} stars selected'
    return dict(columns=columns, rows=rows, hover=hover, status=status, moreRows=more_rows,
                totalRows=total_rows, canLoadAll=can_load_all, star_count=star_count, planet_count=planet_count)


def table_download_lines(table: dict, file_format: str):
    """The table as text lines for a download: csv (quoted cells), tsv or psv."""
    delimiter, quote = DOWNLOAD_FORMATS[file_format]
    yield delimiter.join(table['columns'])
    for row in table['rows']:
        cells = []
        for cell in row:
            if isinstance(cell, list):
                cell = ''.join(cell)
            cells.append(f'{quote}{cell}{quote}')
        yield '\n' + delimiter.join(cells)
