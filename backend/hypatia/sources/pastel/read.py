from hypatia.configs.file_paths import pastel_file
from hypatia.object_params import ObjectParams, SingleParam
from hypatia.sources.simbad.batch import get_star_data_batch

requested_params = {'logg', 'teff', 'bmag', 'vmag', 'jmag', 'hmag', 'ksmag'}
param_to_unit = {'logg': '', 'teff': 'K', 'bmag': 'mag', 'vmag': 'mag',
                 'jmag': 'mag', 'hmag': 'mag', 'ksmag': 'mag'}


def float_or_str(value: str) -> float | str:
    try:
        return float(value)
    except ValueError:
        return value

def read_pastel_file(delimiter: str = '|', null_value: str = '') \
        -> tuple[list[str], list[dict[str, float | int | str]]]:
    pastel_ids = []
    row_dicts = []
    columns_names = []
    with open(pastel_file, 'r') as file:
        for line in file.readlines():
            if line.startswith('#'):
                continue
            elif line.startswith('ID') and not columns_names:
                columns_names = [column_name.strip().lower() for column_name in line.strip().split(delimiter)]
                continue
            else:
                stripped_line = line.strip()
                if stripped_line != '':
                    row_data = [datum.strip() for datum in line.strip().split(delimiter)]
                    row_dict = {columns_name: float_or_str(row_datum) for columns_name, row_datum in
                                zip(columns_names, row_data) if row_datum != ''}
                    pastel_id = row_dict.pop('id')
                    pastel_ids.append(pastel_id)
                    row_dicts.append(row_dict)
    return pastel_ids, row_dicts


def load_from_file(verbose: bool) -> tuple[dict[str, ObjectParams], dict[str, set[str]]]:
    data = {}
    main_id_to_pastel_ids = {}
    if verbose:
        print(f'Loading Pastel data from file: {pastel_file}')
    pastel_ids, row_dicts = read_pastel_file()
    star_docs = get_star_data_batch(search_ids=[(pastel_id,) for pastel_id in pastel_ids], test_origin='pastel',
                                    override_interactive_mode=True)
    for pastel_id, star_doc, row_data in zip(pastel_ids, star_docs, row_dicts):
        star_id = star_doc['_id']
        if star_id in main_id_to_pastel_ids.keys():
            main_id_to_pastel_ids[star_id].add(pastel_id)
        else:
            main_id_to_pastel_ids[star_id] = {pastel_id}
        row_data = {key.lower(): value for key, value in row_data.items()}
        ref = f'Pastel Catalog ({pastel_id}): {row_data['author']} {row_data['bibcode']}'
        all_params_this_star = ObjectParams()
        if star_id not in data.keys():
            data[star_id] = ObjectParams()
        params_this_star = data[star_id]
        for param_type in requested_params:
            if param_type in row_data:
                params_this_star[param_type] = SingleParam.strict_format(param_name=param_type,
                                                                         value=row_data[param_type],
                                                                         ref=ref,
                                                                         units=param_to_unit[param_type])
        if all_params_this_star:
            data[star_id] = all_params_this_star
    if verbose:
        print('  Pastel data Loaded')
    return data, main_id_to_pastel_ids


if __name__ == '__main__':
    pastel_data, simbad_id_to_pastel_ids = load_from_file(verbose=True)
