import os
import pickle

from hypatia.tools.table_read import row_dict
from hypatia.tools.star_names import star_name_format
from hypatia.config import ref_dir, output_products_dir
from hypatia.object_params import ObjectParams, SingleParam


# When updating a new Pastel file, change the filename on Line 35 and the delimiter on Line 55.
# The file needs to have ID, Bmag, Vmag, Jmag, Hmag, Ksmag, Teff, logg, Author, and bibcode which can come from Vizier.
class Pastel:
    # these names cover the majority of unique names in Pastel reference file
    star_name_types = {"hip", "2mass", 'bd', "hd", "tyc", "cd", "*", "g", "hat", "koi", "k2", "kepler", "v*"}
    requested_params = {"logg", "teff", "bmag", "vmag", "jmag", "hmag", "ksmag"}
    parma_to_unit = {"logg": "", "teff": "K", "bmag": "mag", "vmag": "mag",
                     "jmag": "mag", "hmag": "mag", "ksmag": "mag"}

    def __init__(self, auto_load: bool = False, from_scratch: bool = False, verbose: bool = True):
        self.file_name = os.path.join(ref_dir, "Pastel20.psv")
        self.processed_pickle_file = os.path.join(output_products_dir, 'pastel_processes.pkl')
        self.data = None
        self.verbose = verbose
        self.from_scratch = from_scratch
        if auto_load:
            self.load(from_scratch=from_scratch)

    def load(self, from_scratch: bool = None):
        self.data = {}
        if from_scratch is None:
            from_scratch = self.from_scratch
        if self.verbose:
            print("    Loading Pastel data")
        if from_scratch or not os.path.exists(self.processed_pickle_file):
            for pastel_id, row_data in row_dict(self.file_name, delimiter="|", key="ID",
                                                null_value="", inner_key_remove=True).items():
                if pastel_id == 'comments':
                    continue
                row_data = {key.lower(): value for key, value in row_data.items()}
                try:
                    star_type, star_id = star_name_format(pastel_id)
                except ValueError:
                    continue
                name_type = star_type.lower()
                if name_type not in self.star_name_types:
                    continue
                if name_type not in self.data.keys():
                    self.data[name_type] = {}
                ref = f"Pastel Catalog ({pastel_id}): {row_data['author']} {row_data['bibcode']}"
                all_params_this_star = ObjectParams()
                if star_id not in self.data[name_type]:
                    self.data[name_type][star_id] = ObjectParams()
                params_this_star = self.data[name_type][star_id]
                for param_type in self.requested_params:
                    if param_type in row_data:
                        params_this_star[param_type] = SingleParam.strict_format(param_name=param_type,
                                                                                 value=row_data[param_type],
                                                                                 ref=ref,
                                                                                 units=self.parma_to_unit[param_type])
                if all_params_this_star:
                    self.data[name_type][star_id] = all_params_this_star

            pickle.dump(self.data, open(self.processed_pickle_file, 'wb'))
        else:
            self.data = pickle.load(open(self.processed_pickle_file, "rb"))
        if self.verbose:
            print("    Pastel data Loaded")

    def get_record_from_aliases(self, aliases: list[str]) -> dict | None:
        found_names = {}
        for star_name in aliases:
            for pastel_name_type in self.star_name_types:
                if star_name.lower().startswith(pastel_name_type):
                    if not (star_name[0] == "*" and star_name[1] == "*"):
                        found_names[pastel_name_type] = star_name
                        break
        pastel_params = None
        if found_names:
            for this_star_name_type, this_star_name in found_names.items():
                try:
                    name_type, formatted_id = star_name_format(this_star_name, key=this_star_name_type)
                except ValueError:
                    pass
                else:
                    by_ids_for_this_name_type = self.data[this_star_name_type]
                    if formatted_id in by_ids_for_this_name_type.keys():
                        pastel_params = by_ids_for_this_name_type[formatted_id]
                        """
                        No need to keep searching, there will only be star_type, star_id combination for the pastel 
                        reference data.
                        """
                        break
        return pastel_params


if __name__ == "__main__":
    # from_scratch is needed to delete the pkl file and test a new imported file
    pastel = Pastel(auto_load=True, from_scratch=True)
