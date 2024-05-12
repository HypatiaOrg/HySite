import os
import pickle

import pandas as pd

from hypatia.config import hdf5_data_dir


def read_composition_file(filepath: str):
    element_data = pd.read_hdf(filepath, key='compositions')
    return element_data


def read_pickle_file(filepath: str):
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    return data


if __name__ == '__main__':
    hashable_filepath = os.path.join(hdf5_data_dir, "hashtable.shelf")
    hashtable = read_pickle_file(hashable_filepath)

    file_number = 2  # 1 is absolute elemental abundances
    composition_filepath = os.path.join(hdf5_data_dir, f"compositions.{file_number}.h5")
    composition_data = read_composition_file(filepath=composition_filepath)
    for field_name in composition_data:
        data_column = composition_data[field_name]
        print(f'{field_name} has (min, max) of ({data_column.min()}, {data_column.max()})')
