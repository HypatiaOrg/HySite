import os
import pickle
import shutil
import datetime
from warnings import warn

from hypatia.tools.table_read import ClassyReader
from hypatia.tools.color_text import catalog_name_text
from hypatia.sources.simbad.batch import get_star_data_batch
from hypatia.configs.source_settings import allowed_name_types
from hypatia.tools.exceptions import ElementNameErrorInCatalog
from hypatia.elements import element_rank, ElementID, iron_id, iron_ii_id, iron_nlte_id
from hypatia.configs.file_paths import abundance_dir, default_catalog_file, cat_pickles_dir
from hypatia.sources.catalogs.solar_norm import (solar_norm_dict, ratio_to_element,
                                                 un_norm_x_over_fe, un_norm_x_over_h, un_norm_abs_x)


def get_catalogs(from_scratch=False, catalogs_file_name=None, local_abundance_dir=None, verbose=False):
    """
    Smashes together all the catalogs into a dictionary,
    including the solar normalization as a key, while un-normalizing
    all the abundances to be on an absolute scale,
    to be handed to the CatalogQuery class.
    """

    if catalogs_file_name is None or catalogs_file_name == 'catalog_file.csv':
        full_catalog_file_name = default_catalog_file
    else:
        full_catalog_file_name = catalogs_file_name
    if local_abundance_dir is None:
        local_abundance_dir = abundance_dir
    catalog_info = ClassyReader(full_catalog_file_name)
    long_catalog_names = {}
    catalog_norm = {}
    for index, short_name in list(enumerate(catalog_info.short)):
        long_catalog_names[short_name] = catalog_info.long[index]
        catalog_norm[short_name] = catalog_info.norm[index]

    # put the catalogs in alphabetical order like a human
    catalog_names = sorted([short_name for short_name in catalog_info.short])

    if from_scratch:
        # Make a dictionary of all the catalogs listed in the file in 'catalogs_file_name'
        catalog_dict = {key: Catalog(catalog_name=key,
                                     long_name=long_catalog_names[key],
                                     norm_key=catalog_norm[key],
                                     catalogs_file_name=full_catalog_file_name,
                                     verbose=verbose,
                                     local_abundance_dir=local_abundance_dir)
                        for key in catalog_names}
        for cat_data in catalog_dict.values():
            cat_data.un_normalize()

    else:
        catalog_pickle_files = [(catalog_name, os.path.join(cat_pickles_dir,
                                                            f'{catalog_name.lower().replace(" ", "")}.pkl'))
                                for catalog_name in catalog_names]
        catalog_dict = {}
        for catalog_name, catalog_pickle_file in catalog_pickle_files:
            catalog_dict[catalog_name] = pickle.load(open(catalog_pickle_file, 'rb'))

    return catalog_dict


class Catalog:
    def __init__(self, catalog_name, long_name, norm_key, catalogs_file_name='', verbose=False,
                 local_abundance_dir=None):
        self.catalog_name = catalog_name
        self.verbose = verbose
        if self.verbose:
            print(f'{catalog_name_text(self.catalog_name)} is being loaded')
        self.long_name = long_name
        self.norm_key = norm_key
        self.catalogs_file_name = catalogs_file_name
        if local_abundance_dir is None:
            self.abundance_dir = abundance_dir
        else:
            self.abundance_dir = local_abundance_dir
        self.file_path = os.path.join(self.abundance_dir, catalog_name.replace(' ', '').lower())
        self.save_file_name = os.path.join(cat_pickles_dir, catalog_name.replace(' ', '').lower() + '.pkl')
        self.main_star_ids_unique_groups = None
        self.unique_star_groups = None
        self.name_update_needed = None

        if os.path.lexists(self.file_path + '.csv'):
            self.file_path += '.csv'
            self.delimiter = ','
        elif os.path.lexists(self.file_path + '.tsv'):
            self.file_path += '.tsv'
            self.delimiter = '|'
        else:
            raise FileExistsError(f'The file: {self.file_path} was not found')

        # use ClassyReader, add attributes of the file (i.e., the element columns) to the raw_data attribute
        self.raw_data = ClassyReader(self.file_path, delimiter=self.delimiter)
        if hasattr(self.raw_data, 'comments'):
            self.comments = self.raw_data.comments
        else:
            self.comments = None
        # set a single normalization dictionary for the catalog
        self.norm_dict = solar_norm_dict[self.norm_key]

        """ Parse star names"""
        # determine the star name data-type and convert the star names to the SIMBAD format
        all_attributes = set(self.raw_data.__dict__)
        name_types = allowed_name_types & all_attributes
        if 'simbad_id' in name_types:
            # Catalogs that have been processed will have the SIMBAD ID as the star name
            self.star_names_type = 'simbad_id'
            self.raw_data.original_star_names = self.raw_data.original_name
            input_names = self.raw_data.simbad_id
            self.star_docs = get_star_data_batch([(simbad_name,) for simbad_name in input_names],
                                                 test_origin=f'{self.catalog_name}')
        elif len(name_types) == 0:
            raise NameError('The star column name is not one of the expected names.')
        elif len(name_types) == 1:
                self.star_names_type = name_types.pop()
                self.raw_data.original_star_names = getattr(self.raw_data, self.star_names_type)
                input_names = self.raw_data.original_star_names
                self.star_docs = get_star_data_batch([(simbad_name,) for simbad_name in input_names],
                                                     test_origin=f'{self.catalog_name}')
        else:
            sorted_names = sorted(name_types)
            self.star_names_type = sorted_names[0]
            self.raw_data.original_star_names = getattr(self.raw_data, self.star_names_type)
            input_names = [tuple(name_for_one_star) for name_for_one_star in zip(*[getattr(self.raw_data, name)
                                                                                   for name in sorted_names])]
            self.star_docs = get_star_data_batch(input_names, test_origin=f'{self.catalog_name}')
        # double-check that this name is still the primary name in SIMBAD
        self.star_names = [star_doc['_id'] for star_doc in self.star_docs]
        # add the star names to the raw_data object
        self.raw_data.star_names = self.star_names

        """ Reshape data for use in the class """
        # Maps the XH key to an element X
        self.element_to_ratio_name = {}
        self.absolute_elements = set()
        self.element_id_to_un_norm_func = {}
        non_element_keys = {'comments', 'original_name', self.star_names_type}
        for key in self.raw_data.keys:
            if key in non_element_keys:
                # these are not element keys, so we skip them.
                continue
            try:
                element_id, un_norm_func_name = ratio_to_element(key)
            except KeyError as e:
                print(e)
                raise ElementNameErrorInCatalog(f'Key: {key} in catalog: {self.catalog_name} is not a recognized element key.')
            else:
                formatted_key = f'{element_id}'
                if formatted_key != key:
                    setattr(self.raw_data, formatted_key, self.raw_data.__getattribute__(key))
                    self.raw_data.__setattr__(formatted_key, self.raw_data.__getattribute__(key))
                    delattr(self.raw_data, key)
                    key = formatted_key
                if un_norm_func_name == 'un_norm_abs_x':
                    self.absolute_elements.add(element_id)
                self.element_to_ratio_name[element_id] = key
                self.element_id_to_un_norm_func[element_id] = un_norm_func_name

        self.element_keys = set(self.element_to_ratio_name.keys())
        self.element_ratio_keys = {self.element_to_ratio_name[key] for key in self.element_to_ratio_name}
        if iron_ii_id in self.element_keys:
            warn(f'The Fe_II element in {self.catalog_name} is not allowed in the catalog data.')
            self.element_keys.remove(iron_ii_id)
            del self.element_to_ratio_name[iron_ii_id]
        """
            Creates a unique dictionary for each star in the catalog such that the element data can be
            more easily accessed (not by index) -- ultimately this preps it for CatalogQuery.
            Also, get rid of null values like 99.99 and "".
        """
        self.raw_star_data = [
            {ElementID.from_str(element_key): self.raw_data.__getattribute__(element_key)[catalog_index]
             for element_key in self.element_ratio_keys
             if self.raw_data.__getattribute__(element_key)[catalog_index] not in {99.99, ''}}
            for catalog_index in range(len(self.raw_data.star_names))
        ]
        self.star_names = self.raw_data.star_names
        self.original_star_names = self.raw_data.original_star_names
        if self.verbose:
            print(f'   Loaded the data for the {self.catalog_name} - star name type: {self.star_names_type}')

        # Initialize the un-normalized data and data products from other methods.
        self.abs_star_data = []
        self.unreferenced_stars = []
        self.unreferenced_stars_raw_index = []

    def remove_elements(self, lost_element: ElementID, reason):
        self.element_ratio_keys.remove(self.element_to_ratio_name[lost_element])
        self.element_keys.remove(lost_element)
        warn(f'Element: {lost_element} was removed from the catalog: {self.catalog_name} because {reason}')

    def un_normalize(self):
        # check to see if the normalization will cover all the elements in this catalog.
        if self.norm_dict is not None:
            for main_star_id, original_star_name, star_dict \
                    in zip(self.star_names, self.original_star_names, self.raw_star_data):
                # get the keys that are not elements, such as star_name and comments
                element_dict = {element_id: star_dict[element_id]
                                for element_id in self.element_keys & set(star_dict.keys())}

                # the heart of the un-normalization process
                un_norm_dict = {}
                key_set = set(element_dict.keys())
                for element_id in key_set:
                    un_norm_func_name = self.element_id_to_un_norm_func[element_id]
                    element_value = element_dict[element_id]
                    if un_norm_func_name == 'un_norm_abs_x':
                         un_norm_dict[element_id] = un_norm_abs_x(element_value)
                    else:
                        # these elements require a solar value to un-normalize
                        solar_value = None
                        if element_id in self.norm_dict.keys():
                            solar_value = self.norm_dict[element_id]
                        elif element_id.name_lower:
                            default_element = ElementID(name_lower=element_id.name_lower,
                                                        ion_state=element_id.ion_state, is_nlte=False)
                            if default_element in self.norm_dict.keys():
                                solar_value = self.norm_dict[default_element]
                        if solar_value is None:
                            self.remove_elements(element_id, 'no solar value available')
                            continue
                        if un_norm_func_name == 'un_norm_x_over_h':
                            un_norm_dict[element_id] = un_norm_x_over_h(relative_x_over_h=element_value,
                                                                        solar_x=solar_value)
                        elif un_norm_func_name == 'un_norm_x_over_fe':
                            if element_id.is_nlte and iron_nlte_id in key_set:
                                iron_value = element_dict[iron_nlte_id]
                            elif iron_id not in key_set:
                                raise KeyError(f'Element: {element_id} in catalog: {self.catalog_name} star:{original_star_name} requires [Fe/H] to un-normalize.')
                            else:
                                iron_value = element_dict[iron_id]
                            un_norm_dict[element_id] = un_norm_x_over_fe(relative_x_over_fe=element_value,
                                                                         relative_fe_over_h=iron_value,
                                                                         solar_x=solar_value)
                        else:
                            raise KeyError(f'Un-normalization function: {un_norm_func_name} not recognized for {self.catalog_name} star:{original_star_name}')
                # rewrite the dict to include the non-element keys like star names.
                self.abs_star_data.append(un_norm_dict)

    def find_double_listed(self):
        self.unique_star_groups = []
        self.main_star_ids_unique_groups = []
        for main_star_id, original_name, element_data in zip(self.star_names, self.original_star_names, self.raw_star_data):
            # find a group that the star is not in and add it to that group, make new groups as needed.
            for group_num, main_star_ids in list(enumerate(self.main_star_ids_unique_groups)):
                if main_star_id not in main_star_ids:
                    main_star_ids.add(main_star_id)
                    self.unique_star_groups[group_num].append((main_star_id, original_name, element_data))
                    # we found a group for the star, so we can stop looking.
                    break
            else:
                # what happen if the break statement above is not reached. 
                self.main_star_ids_unique_groups.append({main_star_id})
                self.unique_star_groups.append([(main_star_id, original_name, element_data)])

    def write_catalog(self, output_dir: str, target='raw', update_catalog_list=False, add_to_git=False):
        if target.lower() in {'unnorm', 'abs', 'absolute'}:
            target = 'un_norm'
        now = datetime.datetime.now()
        date_string = f"{'%02i' % now.day}_{'%02i' % now.month}_{'%04i' % now.year}"
        if target == 'raw':
            star_lists = [zip(self.star_names, self.original_star_names, self.raw_star_data)]
            comments = [f'{date_string} Raw data (original solar normalization) output from the Catalog class in the ' +
                        'Hypatia package.']
            new_short_name = '_raw_'
        elif target == 'un_norm':
            star_lists = [zip(self.star_names, self.original_star_names, self.abs_star_data)]
            comments = [f'{date_string} Absolute (un-normalized) data output from the Catalog class in the Hypatia ' +
                        'package']
            new_short_name = '_absolute_'
        elif target == 'unique':
            star_lists = self.unique_star_groups
            total_string = str('%02i' % len(self.unique_star_groups))
            comments = [f'XX of {total_string} {date_string} ' +
                        'Raw data (original solar normalization) data output from the Catalog class ' +
                        'in the Hypatia package']
            new_short_name = '_XX_of_' + total_string + '_unique_'
        else:
            raise KeyError(f"'{target}' was not one of the expected target types for writing a catalog data")
        new_short_name = self.catalog_name + new_short_name + date_string
        file_name = new_short_name.replace(' ', '').lower() + '.csv'
        short_names_list = []
        if self.comments is not None:
            comments.extend(self.comments)
        for list_index, star_list in list(enumerate(star_lists)):
            if target == 'unique':
                this_list_number = str('%02i' % (list_index + 1))
                comments[0] = this_list_number + comments[0][2:]
                new_short_name = self.catalog_name + '_' + this_list_number + \
                                 new_short_name[len(self.catalog_name) + 3:]
                short_names_list.append(new_short_name)
                file_name = self.catalog_name.replace(' ', '').lower() + '_' + this_list_number + \
                            file_name[len(self.catalog_name.replace(' ', '')) + 3:]
            else:
                short_names_list.append(new_short_name)
            ordered_element_list = sorted(self.element_keys, key=element_rank)
            if target == 'un_norm':
                header_list = [f'{element}_A' for element in ordered_element_list]
            else:
                header_list = []
                for element_string in ordered_element_list:
                    element_id = self.element_to_ratio_name[element_string]
                    un_norm_type = self.element_id_to_un_norm_func[element_string]
                    if un_norm_type == 'un_norm_abs_x':
                        header_list.append(f'{element_id}_A')
                    elif un_norm_type == 'un_norm_x_over_h':
                        header_list.append(f'{element_id}_H')
                    elif un_norm_type == 'un_norm_x_over_fe':
                        header_list.append(f'{element_id}_Fe')
                    else:
                        raise KeyError(f'Un-normalization function: {un_norm_type} not recognized for {self.catalog_name}')
            header = ','.join(['simbad_id', 'original_name'] + header_list) + '\n'
            body = []
            for main_star_id, original_name, element_data in star_list:
                single_line = f'{main_star_id},{original_name},' + ','.join([str(element_data[element])
                                                                             if element in element_data.keys()
                                                                             else ''
                                                                             for element in ordered_element_list])
                body.append(single_line + '\n')
            full_file_and_path = os.path.join(output_dir, file_name)
            with open(full_file_and_path, 'w') as f:
                for comment in comments:
                    f.write(f'# {comment}\n')
                f.write(header[:-1] + '\n')
                [f.write(single_line) for single_line in body]
            if add_to_git:
                os.system(f'git add {full_file_and_path}')

        if update_catalog_list:
            long_name = self.long_name
            norm_name = self.norm_key
            target_file = os.path.join(self.abundance_dir, self.catalogs_file_name)
            old_file = os.path.join(self.abundance_dir, 'old_' + os.path.basename(self.catalogs_file_name))
            shutil.copyfile(target_file, old_file)
            header = 'short,long,norm\n'
            catalog_name_data = ClassyReader(old_file)
            body = []
            for line_index in range(len(catalog_name_data.short)):
                test_short_name = catalog_name_data.short[line_index]
                if test_short_name == self.catalog_name:
                    for new_short_name in short_names_list:
                        body.append(new_short_name + ',' + long_name + ',' + norm_name + '\n')
                else:
                    body.append(test_short_name + ',' + catalog_name_data.long[line_index] + ',' +
                                catalog_name_data.norm[line_index] + '\n')
            with open(os.path.join(target_file), 'w') as f:
                f.write(header)
                [f.write(single_line) for single_line in body]

    def save(self, save_file_name=None):
        if save_file_name is not None:
            self.save_file_name = save_file_name
        dirname = os.path.dirname(self.save_file_name)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        pickle.dump(self, open(self.save_file_name, 'wb'))


if __name__ == '__main__':
    test_cat = Catalog(catalog_name='nissen97',
                       long_name='Nissen & Schuster (1997)',
                       norm_key='neuforge97',
                       verbose=True)
    test_cat.un_normalize()
