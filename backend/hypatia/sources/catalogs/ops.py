import os
import shutil

from hypatia.tools.table_read import row_dict
from hypatia.tools.color_text import file_name_text
from hypatia.configs.file_paths import (ref_dir, abundance_dir, default_catalog_file, new_abundances_dir,
                                        new_catalogs_file_name)


def short_name_to_filename(short_name: str, abundance_dir_name: str = abundance_dir):
    csv_file_name = os.path.join(abundance_dir_name, short_name.lower() + '.csv')
    if os.path.exists(csv_file_name):
        return csv_file_name
    tsv_file_name = os.path.join(abundance_dir_name, short_name.lower() + '.tsv')
    if os.path.exists(tsv_file_name):
        return tsv_file_name
    raise FileNotFoundError(f'File not found for short name: {short_name} at\n{csv_file_name}\n{tsv_file_name}')


def make_cat_record(short: str, long: str, norm: str):
    _, year_slice = long.rsplit('(', 1)
    year_str = ''
    for char in year_slice:
        if char.isdigit():
            year_str += char
        elif year_str:
            break
    if year_str:
        year = int(year_str)
    else:
        raise ValueError(f'Year not found in the long name: {long}')
    return {'author': long, 'year': year, 'id': short, 'original_norm_id': norm}


def export_to_records(catalog_input_file: str = default_catalog_file, requested_catalogs: list[str] = None):
    row_data = row_dict(catalog_input_file, delimiter=',', inner_key_remove=False, key='short')
    if requested_catalogs is None:
        requested_catalogs = row_data.keys()
    return {catalog_name: make_cat_record(**row_data[catalog_name]) for catalog_name in requested_catalogs}


class CatOps:
    def __init__(self, cat_file: str | None = None, abundance_dir_for_reset: str = abundance_dir,
                 load:bool = True, verbose: bool = True):
        self.verbose = verbose
        if cat_file is None:
            self.cat_file = default_catalog_file
            self.abundance_dir = abundance_dir
        else:
            self.cat_file = cat_file
            self.abundance_dir = abundance_dir_for_reset
        self.cat_dict = None
        self.reset_cat_dict = None
        self.processed_files = None
        self.original_files = None
        if load:
            self.load()

    def load(self):
        with open(self.cat_file, 'r') as f:
            cat_lines = f.readlines()
        self.cat_dict = {}
        for a_line in cat_lines[1:]:
            short, long, norm = a_line.split(',')
            try:
                # This process is used by the summary upload.
                # It checks to see if the year value can be found in the long name
                make_cat_record(short=short, long=long, norm=norm)
            except ValueError:
                error_msg = f'Error in the catalog file: {self.cat_file}\n'
                error_msg += f'Error in the line: {a_line}\n'
                error_msg += f"Is there a 'year' in the long name and is it in parentheses?"
                raise ValueError(error_msg)
            self.cat_dict[short.lower().strip()] = {'long': long.strip(), 'norm': norm.lower().strip()}
        if self.verbose:
            print('\nLoading the catalog file:', self.cat_file)
            print('This file has', len(self.cat_dict.keys()), 'entries.\n')

    def write(self, full_cat_file=None, cat_dict=None):
        if full_cat_file is None:
            full_cat_file = self.cat_file
        if cat_dict is None:
            cat_dict = self.cat_dict
        with open(full_cat_file, 'w') as f:
            f.write('short,long,norm\n')
            for short in sorted(cat_dict.keys()):
                long = cat_dict[short]['long']
                norm = cat_dict[short]['norm']
                f.write(short + ',' + long + ',' + norm + '\n')
        if self.verbose:
            print('Writing the catalog file:', full_cat_file)
            print('This file has', len(cat_dict.keys()), 'entries.\n')

    def standardize(self, data_dir=None):
        if data_dir is None:
            data_dir = abundance_dir
        files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
        for file in files:
            os.rename(os.path.join(data_dir, file), os.path.join(data_dir, file.lower()))
        if self.verbose:
            print('\nAll the catalog dat files have been renamed to have all lowercase filenames,' +
                  'the expected standard.\n')

    def make_subset_file(self, short_name_list, subset_local_cat_file=None):
        if subset_local_cat_file is None:
            subset_local_cat_file = 'subset_catalog_file.csv'
        full_subset_cat_file = os.path.join(ref_dir, subset_local_cat_file)
        short_names = set(self.cat_dict.keys())
        names_to_use = set()
        for short_name in short_name_list:
            formatted_short_name = short_name.lower().strip()
            if formatted_short_name in short_names:
                names_to_use.add(formatted_short_name)
            else:
                raise KeyError('The short name:' + str(formatted_short_name) +
                               ' was not found in the available names: ' + str(short_names))
        if self.verbose:
            print('Writing a subset catalog file:', subset_local_cat_file)
        self.write(full_cat_file=full_subset_cat_file, cat_dict={short: self.cat_dict[short] for short in names_to_use})

    def reset_cat_file(self):
        # First reset the catalog file
        if self.verbose:
            print('\nResetting the catalog file..')
        self.reset_cat_dict = {}
        self.processed_files = set()
        self.original_files = set()
        for short in self.cat_dict.keys():
            processed_file = short_name_to_filename(short, abundance_dir_name=self.abundance_dir)
            reset_short_name, *_ = short.split('_')
            if '_' in short:
                self.processed_files.add(processed_file)
                self.original_files.add(short_name_to_filename(reset_short_name, abundance_dir_name=self.abundance_dir))
            else:
                self.original_files.add(processed_file)
            self.reset_cat_dict[reset_short_name] = self.cat_dict[short]
        self.write(full_cat_file=new_catalogs_file_name, cat_dict=self.reset_cat_dict)
        if self.cat_file == default_catalog_file:
            os.remove(self.cat_file)
            if self.verbose:
                print('The original catalog file was removed:', file_name_text(self.cat_file))
        if self.verbose:
            print('The reset catalog file was written to:', file_name_text(new_catalogs_file_name))
        # move the original files
        from_dir = self.abundance_dir
        to_dir = new_abundances_dir
        if not os.path.exists(to_dir):
            os.makedirs(to_dir)
        if from_dir != to_dir:
            for file in sorted(self.original_files):
                filename = os.path.basename(file)
                shutil.move(file, os.path.join(to_dir, filename))
                if self.verbose:
                    print('  Moved:', file_name_text(file), '\n  to:', file_name_text(to_dir))
        # delete the processed files
        for file in sorted(self.processed_files):
            os.remove(file)
            if self.verbose:
                print('  Removed:', file_name_text(file))
        if self.verbose:
            print('The catalog files have been reset.\n')


if __name__ == '__main__':
    # cat_object = CatOps(verbose=True)
    # cat_object.standardize()
    # cat_object.make_subset_file(short_name_list=['luck 15'])
    test_records = export_to_records()
