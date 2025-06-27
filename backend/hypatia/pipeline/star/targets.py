import os
import glob

import toml

from hypatia.configs.file_paths import targets_web_dir
from hypatia.sources.simbad.batch import get_star_data_batch


name_prefixs = {
    'tic_id': 'TIC ',
    'gaia_dr2_id': 'Gaia DR2 ',
    'gaia_dr3_id': 'Giaa DR3 ',
    'hip_name': 'HIP ',
    'tyc_name': 'TYC ',
}

required_fields = {'handle', 'title', 'ref', 'names'}
not_for_summary_fields = {'names', 'id_to_origin', 'ids'}


def convert_hwo_file(scr: str, dest: str, **kwargs):
    all_data = {**kwargs}
    with open(scr) as f:
        header = [column.strip() for column in f.readline().strip().split('|')]
        all_names = []
        for line in f.readlines():
            names = []
            for column_name, star_id in zip(header, line.strip().split('|')):
                star_id = star_id.strip()
                if star_id != 'null':
                    names.append(name_prefixs.get(column_name, '') + star_id)
            all_names.append('|'.join(names))
    all_data['names'] = all_names
    with open(dest, 'w') as f:
        toml.dump(all_data, f)


def read_all_targets_files():
    toml_files = list(glob.glob(os.path.join(targets_web_dir, '*.toml')))
    target_data = {}
    for toml_file in toml_files:
        with open(toml_file, 'r') as f:
            data = toml.load(f)
            for field in required_fields:
                if field not in data:
                    raise ValueError(f'The field "{field}" is required in the TOML file {toml_file}.')
            if 'description' not in data:
                data['description'] = ''
            all_names = data.get('names', [])
            star_docs = get_star_data_batch(search_ids=[tuple([one_name.strip() for one_name in name_line.split('|')])
                                                        for name_line in all_names],
                                            test_origin='targets import')
            data['id_to_origin'] = {star_doc['_id']: star_doc for star_doc in star_docs if star_doc is not None}
            data['ids'] = set(star_doc['_id'] for star_doc in star_docs)
            target_data[data['handle']] = data
    return target_data


if __name__ == '__main__':
    # input_file = os.path.join(targets_web_dir, 'temp.psv')
    # output_file = os.path.join(targets_web_dir, 'hwo_tier1.toml')
    # convert_hwo_file(input_file, output_file,
    #                  description='This file contains the names of the stars in the HWO Tier 1 catalog.',
    #                  handle='hwo_tier1',
    #                  title='HWO Tier 1',
    #                  version='1.0',
    #                  date='2025-06-27',
    #                  ref='Hypatia Team',
    #                  )
    targets = read_all_targets_files()
