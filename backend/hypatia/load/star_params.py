import os
import pickle

from statistics import mean, stdev
from hypatia.config import ref_dir
from hypatia.tools.star_names import star_name_format
from hypatia.load.table_read import row_dict, get_table_data


class Xhip:
    def __init__(self, auto_load=False):
        self.xhip_file_name = os.path.join(ref_dir, "xhip.csv")
        self.ref_data = None
        self.comments = None
        self.available_hip_names = None
        if auto_load:
            self.load()

    def load(self):
        """
        X Hip - it has two types of null values 99.99 and ''
        """
        raw_data = row_dict(self.xhip_file_name, key='HIP', delimiter=",", null_value=99.99)
        if "comments" in raw_data.keys():
            self.comments = raw_data['comments']
            del raw_data['comments']
        self.ref_data = {xhip_key: {param_key: raw_data[xhip_key][param_key] for param_key in raw_data[xhip_key].keys()
                                    if raw_data[xhip_key][param_key] != ""} for xhip_key in raw_data.keys()}
        if self.comments is not None:
            self.ref_data["comments"] = self.comments
        self.available_hip_names = set(self.ref_data.keys())


# When updating a new Pastel file, change the filename on Line 35 and the delimiter on Line 55.
# The file needs to have ID, Bmag, Vmag, Jmag, Hmag, Ksmag, Teff, logg, Author, and bibcode which can come from Vizier.
class Pastel:
    def __init__(self, auto_load=False, from_scratch=False):
        self.pastel_file_name = os.path.join(ref_dir, "Pastel20.psv")
        self.pastel_processed_pickle_file = os.path.join(ref_dir, 'pastel_processes.pkl')
        self.pastel_raw = None
        self.pastel_ave = None
        self.pastel_star_names = None
        self.comments = None
        if auto_load:
            self.load(from_scratch=from_scratch)

    def load(self, from_scratch=False):
        """
        Pastel - There can be several entries per star_name so we need to average those entries. An additional
        is that some entries in this catalog are null, denoted by an empty string '', so weed to filter those out
        and not include them in the averaging.
        """
        if from_scratch or not os.path.exists(self.pastel_processed_pickle_file):
            self.pastel_ave = {}
            # these names cover the majority of unique names in Pastel
            pastel_dict_names = {"hip", "2mass", 'bd', "hd", "tyc", "cd", "*", "g", "hat", "koi", "k2", "kepler", "v*"}
            # read in the pastel data from a raw reference file
            self.pastel_raw = get_table_data(self.pastel_file_name, delimiter="|")
            # list all the lines for the same hipparcos names in a dictionary with keys of hipparcos names
            pastel_star_names_to_line_indexes = {}
            self.pastel_star_names = {}
            for dict_name in pastel_dict_names:
                pastel_star_names_to_line_indexes[dict_name] = {}
                self.pastel_star_names[dict_name] = set()
            for pastel_index in range(len(self.pastel_raw["ID"])):
                try:
                    star_type, star_id = star_name_format(self.pastel_raw["ID"][pastel_index])
                    if star_type in pastel_dict_names:
                        if star_id in set(pastel_star_names_to_line_indexes[star_type].keys()):
                            pastel_star_names_to_line_indexes[star_type][star_id].append(pastel_index)
                        else:
                            pastel_star_names_to_line_indexes[star_type][star_id] = [pastel_index]
                        self.pastel_star_names[star_type].add(star_id)
                except ValueError:
                    pass
            # make a dictionary of the average values per Hipparcos star for each parameters in the pastel file
            for dict_name in pastel_dict_names:
                self.pastel_ave[dict_name] = {}
                if "comments" in self.pastel_raw.keys():
                    self.comments = self.pastel_raw['comments']
                    del self.pastel_raw['comments']
                for star_id in set(pastel_star_names_to_line_indexes[dict_name].keys()):
                    # middle if-statement accounts for the null value
                    dict_list = [{key: self.pastel_raw[key][pastel_index] for key in self.pastel_raw.keys()
                                  if self.pastel_raw[key][pastel_index] != ''}
                                 for pastel_index in pastel_star_names_to_line_indexes[dict_name][star_id]]
                    pre_average_dict = {}
                    for line_dict in dict_list:
                        for line_key in line_dict.keys():
                            if line_key in pre_average_dict.keys():
                                pre_average_dict[line_key].append(line_dict[line_key])
                            else:
                                pre_average_dict[line_key] = [line_dict[line_key]]
                    average_dict = {}
                    for name_key in ["ID"]:
                        average_dict[name_key] = pre_average_dict[name_key][0]
                    for name_key in ["Author", "bibcode"]:
                        average_dict[name_key] = pre_average_dict[name_key]
                    for name_key in ["Bmag", "Vmag", "Jmag", "Hmag", "Ksmag", "Teff", "logg"]:
                        if name_key in pre_average_dict.keys():
                            if pre_average_dict[name_key]:
                                average_dict[name_key] = mean(pre_average_dict[name_key])
                            if 1 < len(pre_average_dict[name_key]):
                                average_dict[name_key + "_std"] = stdev(pre_average_dict[name_key])
                    self.pastel_ave[dict_name][star_id] = average_dict
            pastel_data = (self.pastel_ave, self.pastel_raw, self.pastel_star_names)
            pickle.dump(pastel_data, open(self.pastel_processed_pickle_file, 'wb'))
        else:
            pastel_data = pickle.load(open(self.pastel_processed_pickle_file, "rb"))
            (self.pastel_ave, self.pastel_raw, self.pastel_star_names) = pastel_data


class StarParams:
    def __init__(self):
        self.hip_file_name = os.path.join(ref_dir, "hipparcos.tsv")
        self.hip = row_dict(self.hip_file_name, key='HIP', delimiter="|", null_value="")


if __name__ == "__main__":
    # sp = StarParams(verbose=True)
    xhip = Xhip(auto_load=True)
    # from_scratch is needed to delete the pkl file and test a new imported file
    pastel = Pastel(auto_load=True, from_scratch=True)
