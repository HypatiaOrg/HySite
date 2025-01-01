import os
import shutil

from hypatia.tools.table_read import row_dict
from hypatia.config import ref_dir, abundance_dir, default_catalog_file, new_abundances_dir


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
    def __init__(self, cat_file=None, load=True, verbose=True):
        self.verbose = verbose
        if cat_file is None:
            self.cat_file = default_catalog_file
        else:
            self.cat_file = cat_file
        self.cat_dict = None
        self.reset_cat_dict = None
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

    def reset_short_name(self):
        self.reset_cat_dict = {}
        for short in self.cat_dict.keys():
            reset_short_name, *_ = short.split('_')
            self.reset_cat_dict[reset_short_name] = self.cat_dict[short]

    def reset_cat_file(self, reset_cat_file_name, delete_old_cat_file=True, delete_and_move=False):
        if self.verbose:
            print('\nResetting the catalog file..')
        self.reset_short_name()
        self.write(full_cat_file=reset_cat_file_name, cat_dict=self.reset_cat_dict)
        if self.verbose:
            print('The reset catalog file was written to:', reset_cat_file_name)

        if delete_and_move:
            from_dir = abundance_dir
            to_dir = new_abundances_dir
            if self.verbose:
                print('\nMoving the unprocessed catalog data files to', to_dir)
            # move all the unprocessed files to the folder that contains the reset version of the catalog file.
            for unprocessed_file in self.reset_cat_dict.keys():
                extension = None
                most_of_the_filename = os.path.join(from_dir, unprocessed_file)
                if os.path.exists(most_of_the_filename + '.csv'):
                    extension = '.csv'
                elif os.path.exists(most_of_the_filename + '.tsv'):
                    extension = '.tsv'
                if extension is None:
                    if self.verbose:
                        print('The file:', unprocessed_file)
                        print('was not found to be moved from', from_dir)
                else:
                    shutil.move(most_of_the_filename + extension, os.path.join(to_dir, unprocessed_file + extension))
                    if self.verbose:
                        print(unprocessed_file + extension + ' was moved from', from_dir, 'to', to_dir)
            # delete any of the remaining processed files
            if self.verbose:
                print('\nDeleting the remaining processed data files in', from_dir)
            for processed_file in self.cat_dict.keys():
                full_processed_file_name = os.path.join(from_dir, processed_file + '.csv')
                if os.path.exists(full_processed_file_name):
                    os.remove(full_processed_file_name)
                    if self.verbose:
                        print('Deleted the processed file:', full_processed_file_name)
        # Delete the old catalog file now that all the data files have been moved without crashing
        if delete_old_cat_file and reset_cat_file_name != self.cat_file and os.path.exists(self.cat_file):
            os.remove(self.cat_file)
            if self.verbose:
                print('The old catalog file was deleted, it was located at:', self.cat_file)
        if self.verbose:
            print('\nCatalog file reset complete.\n')


if __name__ == '__main__':
    # cat_object = CatOps(verbose=True)
    # cat_object.standardize()
    # cat_object.make_subset_file(short_name_list=['luck 15'])
    test_records = export_to_records()
