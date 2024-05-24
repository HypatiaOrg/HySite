import os
import pickle
import shutil
import datetime
from warnings import warn

from hypatia.tools.table_read import ClassyReader
from hypatia.elements import element_rank, ElementID
from hypatia.tools.star_names import calc_simbad_name
from hypatia.tools.exceptions import ElementNameErrorInCatalog
from hypatia.sources.simbad.ops import get_star_data, get_main_id
from hypatia.config import abundance_dir, ref_dir, cat_pickles_dir
from hypatia.sources.catalogs.solar import SolarNorm, ratio_to_element, un_norm


fe_ii = ElementID.from_str("Fe_II")
indicates_mixed_name_types = {"Star", "star", "Stars", "starname", "Starname", "Name", "ID", "Object", "HDBD"}
indicates_single_name_types = {"TYC", "HD", "HIP", "HR", "TrES", "CoRoT", "XO", "HAT", "WASP"}


def get_catalogs(from_scratch=False, catalogs_file_name=None, local_abundance_dir=None, verbose=False):
    """
    Smashes together all the catalogs into a dictionary,
    including the solar normalization as a key, while un-normalizing
    all the abundances to be on an absolute scale,
    to be handed to the CatalogQuery class.
    """

    if catalogs_file_name is None or catalogs_file_name == "catalog_file.csv":
        full_catalog_file_name = os.path.join(ref_dir, "catalog_file.csv")
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
        # Make a dictionary of all the catalogs listed in the file in "catalogs_file_name"
        catalog_dict = {key: Catalog(catalog_name=key,
                                     long_name=long_catalog_names[key],
                                     norm_key=catalog_norm[key],
                                     catalogs_file_name=full_catalog_file_name,
                                     verbose=verbose,
                                     local_abundance_dir=local_abundance_dir)
                        for key in catalog_names}
        for cat_data in catalog_dict.values():
            cat_data.update_star_names()
            cat_data.un_normalize()

    else:
        catalog_pickle_files = [(catalog_name, os.path.join(cat_pickles_dir, f"{catalog_name.lower().replace(" ", '')}.pkl"))
                                for catalog_name in catalog_names]
        catalog_dict = {}
        for catalog_name, catalog_pickle_file in catalog_pickle_files:
            catalog_dict[catalog_name] = pickle.load(open(catalog_pickle_file, 'rb'))

    return catalog_dict


class Catalog:
    def __init__(self, catalog_name, long_name, norm_key, catalogs_file_name="", verbose=False,
                 local_abundance_dir=None):
        self.catalog_name = catalog_name
        self.verbose = verbose
        self.long_name = long_name
        self.norm_key = norm_key
        self.catalogs_file_name = catalogs_file_name
        if local_abundance_dir is None:
            self.file_path = os.path.join(abundance_dir, catalog_name.replace(" ", "").lower())
        else:
            self.file_path = os.path.join(local_abundance_dir, catalog_name.replace(" ", "").lower())
        self.save_file_name = os.path.join(cat_pickles_dir, catalog_name.replace(" ", "").lower() + ".pkl")
        self.main_star_ids_unique_groups = None
        self.unique_star_groups = None
        self.comments = None
        self.name_update_needed = None

        if os.path.lexists(self.file_path + ".csv"):
            self.file_path += ".csv"
            self.delimiter = ","
        elif os.path.lexists(self.file_path + ".tsv"):
            self.file_path += ".tsv"
            self.delimiter = "|"
        else:
            raise FileExistsError(f"The file: {self.file_path} was not found")

        # use ClassyReader, add attributes of the file (i.e., the element columns) to the raw_data attribute
        self.raw_data = ClassyReader(self.file_path, delimiter=self.delimiter)
        # set a single normalization dictionary for the catalog
        self.norm_dict = SolarNorm()(norm_key=self.norm_key)

        """ Parse star names"""
        # determine the star name data-type and convert the star names to the SIMBAD format
        all_attributes = set(self.raw_data.__dict__)
        mixed_name_type = indicates_mixed_name_types & all_attributes
        single_name_type = indicates_single_name_types & all_attributes
        if len(mixed_name_type) == 1:
            attribute_name = list(mixed_name_type)[0]
            self.star_names_type = None
        elif len(single_name_type) == 1:
            attribute_name = list(single_name_type)[0]
            self.star_names_type = attribute_name.lower()
        else:
            raise NameError("The star name type is not one of the expected names.")
        # this a legacy Hypatia system for reading in catalogs with a number of challenges.
        self.raw_data.original_star_names = getattr(self.raw_data, attribute_name)
        converted_star_names = [calc_simbad_name(raw_name, key=self.star_names_type)
                                for raw_name in self.raw_data.original_star_names]
        # the modern system for getting the main star name from the SIMBAD sources.
        self.star_names = [get_main_id(simbad_formatted, test_origin=catalog_name)
                           for simbad_formatted in converted_star_names]
        # add the star names to the raw_data object
        self.raw_data.star_names = self.star_names

        """ Reshape data for use in the class """
        # Maps the XH key to an element X
        self.element_to_ratio_name = {}
        self.absolute_elements = set()
        self.element_id_to_un_norm_func = {}
        for key in self.raw_data.keys:
            if key in {"comments", attribute_name}:
                # these are not element keys, so we skip them.
                continue
            try:
                element_id, un_norm_func_name = ratio_to_element(key)
            except KeyError as e:
                print(e)
                raise ElementNameErrorInCatalog(f"Key: {key} in catalog: {self.catalog_name} is not a recognized element key.")
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
        if fe_ii in self.element_keys:
            warn(f"The Fe_II element in {self.catalog_name} is not allowed in the catalog data.")
            self.element_keys.remove(fe_ii)
            del self.element_to_ratio_name[fe_ii]
        """
            Creates a unique dictionary for each star in the catalog such that the element data can be
            more easily accessed (not by index) -- ultimately this preps it for CatalogQuery.
            Also, get rid of null values like 99.99 and "".
        """
        self.raw_star_data = [
            {ElementID.from_str(element_key): self.raw_data.__getattribute__(element_key)[catalog_index]
             for element_key in self.element_ratio_keys
             if self.raw_data.__getattribute__(element_key)[catalog_index] not in {99.99, ""}}
            for catalog_index in range(len(self.raw_data.star_names))
        ]
        self.star_names = self.raw_data.star_names
        self.original_star_names = self.raw_data.original_star_names
        if self.verbose:
            print("Loaded the data for the", self.catalog_name, "- star name type:", self.star_names_type)

        # Initialize the un-normalized data and data products from other methods.
        self.main_star_names = None
        self.star_docs = None
        self.abs_star_data = []
        self.unreferenced_stars = []
        self.unreferenced_stars_raw_index = []

    def update_star_names(self):
        """
        Get all the star's names, using the SIMBAD sources
        """
        self.main_star_names = []
        self.star_docs = []
        if self.verbose:
            print("Updating the", self.catalog_name, "star names from reference data")
        for element_data, star_name in zip(self.raw_star_data, self.star_names):
            simbad_doc = get_star_data(star_name)
            self.main_star_names.append(simbad_doc['_id'])
            self.star_docs.append(simbad_doc)

    def un_normalize(self):
        # check to see if the normalization will cover all the elements in this catalog.
        if self.norm_dict is not None:
            norm_keys = set(self.norm_dict.keys())
            extra_elements = self.element_keys - norm_keys - self.absolute_elements
            if extra_elements != set():
                print("There are elements in the catalog: " + str(self.catalog_name) + "\n"
                      + "that are not in normalization reference: " + str(self.norm_key) + "\n"
                      + "Namely the elements: " + str(extra_elements) + " .\n"
                      + "   These elements are being omitted from the data output.\n")
                for lost_element in extra_elements:
                    self.element_ratio_keys.remove(self.element_to_ratio_name[lost_element])
                    self.element_keys.remove(lost_element)

        for main_star_id, original_star_name, star_dict \
                in zip(self.main_star_names, self.original_star_names, self.raw_star_data):
            # get the keys that are not elements, such as star_name and comments
            element_dict = {element_id: star_dict[element_id]
                            for element_id in self.element_keys & set(star_dict.keys())}
            # the heart of the un-normalization (un_norm in solar.py)
            un_norm_dict = un_norm(element_dict, self.norm_dict, self.element_id_to_un_norm_func)
            # rewrite the dict to include the non-element keys like star names.
            self.abs_star_data.append(un_norm_dict)

    def find_double_listed(self):
        self.update_star_names()
        self.unique_star_groups = []
        self.main_star_ids_unique_groups = []
        for main_star_id, original_name, element_data in zip(self.main_star_names, self.original_star_names, self.raw_star_data):
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

    def write_catalog(self, output_dir: str, target="raw", update_catalog_list=False, add_to_git=False):
        if target.lower() in {"unnorm", "abs", 'absolute'}:
            target = "un_norm"
        now = datetime.datetime.now()
        date_string = f"{'%02i' % now.day}_{'%02i' % now.month}_{'%04i' % now.year}"
        if target == "raw":
            star_lists = [zip(self.main_star_names, self.original_star_names, self.raw_star_data)]
            comments = [f"{date_string} Raw data (original solar normalization) output from the Catalog class in the " +
                        "Hypatia package."]
            new_short_name = "_raw_"
        elif target == "un_norm":
            star_lists = [zip(self.main_star_names, self.original_star_names, self.abs_star_data)]
            comments = [f"{date_string} Absolute (un-normalized) data output from the Catalog class in the Hypatia " +
                        "package"]
            new_short_name = "_absolute_"
        elif target == "unique":
            star_lists = self.unique_star_groups
            total_string = str("%02i" % len(self.unique_star_groups))
            comments = ["XX of " + total_string + " " + date_string +
                        " Raw data (original solar normalization) data output from the Catalog class " +
                        "in the Hypatia package"]
            new_short_name = "_XX_of_" + total_string + "_unique_"
        else:
            raise KeyError("'" + str(target) + "' was not one of the expected target types for writing a catalog data")
        new_short_name = self.catalog_name + new_short_name + date_string
        file_name = new_short_name.replace(" ", "").lower() + ".csv"
        short_names_list = []
        if self.comments is not None:
            comments.extend(self.comments)
        for list_index, star_list in list(enumerate(star_lists)):
            if target == "unique":
                this_list_number = str("%02i" % (list_index + 1))
                comments[0] = this_list_number + comments[0][2:]
                new_short_name = self.catalog_name + "_" + this_list_number + \
                                 new_short_name[len(self.catalog_name) + 3:]
                short_names_list.append(new_short_name)
                file_name = self.catalog_name.replace(" ", "").lower() + "_" + this_list_number + \
                            file_name[len(self.catalog_name.replace(" ", "")) + 3:]
            else:
                short_names_list.append(new_short_name)
            ordered_element_list = sorted(self.element_keys, key=element_rank)
            if target == "un_norm":
                header_list = [f"{element}_A" for element in ordered_element_list]
            else:
                header_list = [self.element_to_ratio_name[element] for element in ordered_element_list]
            header = ','.join(["simbad_id", 'original_name'] + header_list) + '\n'
            body = []
            for main_star_id, original_name, element_data in star_list:
                single_line = f"{main_star_id},original_name," + ','.join([str(element_data[element])
                                                                           if element in element_data.keys()
                                                                           else ""
                                                                           for element in ordered_element_list])
                body.append(single_line + "\n")
            full_file_and_path = os.path.join(output_dir, file_name)
            with open(full_file_and_path, 'w') as f:
                for comment in comments:
                    f.write("#" + comment + '\n')
                f.write(header[:-1] + "\n")
                [f.write(single_line) for single_line in body]
            if add_to_git:
                os.system(f"git add {full_file_and_path}")

        if update_catalog_list:
            long_name = self.long_name
            norm_name = self.norm_key
            target_file = os.path.join(abundance_dir, self.catalogs_file_name)
            old_file = os.path.join(abundance_dir, "old_" + os.path.basename(self.catalogs_file_name))
            shutil.copyfile(target_file, old_file)
            header = "short,long,norm\n"
            catalog_name_data = ClassyReader(old_file)
            body = []
            for line_index in range(len(catalog_name_data.short)):
                test_short_name = catalog_name_data.short[line_index]
                if test_short_name == self.catalog_name:
                    for new_short_name in short_names_list:
                        body.append(new_short_name + "," + long_name + "," + norm_name + "\n")
                else:
                    body.append(test_short_name + "," + catalog_name_data.long[line_index] + "," +
                                catalog_name_data.norm[line_index] + "\n")
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


if __name__ == "__main__":
    test_cat = Catalog(catalog_name="nissen97",
                       long_name="Nissen & Schuster (1997)",
                       norm_key="neuforge97",
                       verbose=True)
    test_cat.un_normalize()
