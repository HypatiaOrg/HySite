import os

from hypatia.config import ref_dir
from hypatia.tools.table_read import row_dict
from hypatia.sources.gaia.query import GaiaQuery
from hypatia.sources.simbad.ops import get_star_data
from hypatia.object_params import ObjectParams, SingleParam



gaia_dr3_ref = "Gaia DR3 Gaia Collaboration et al. (2016b) and Gaia Collaboration et al. (2022k)"

rename_params = {"ra_epochj2000": "raj2000", "dec_epochj2000": "decj2000",
                 "pmra": "pm_ra", "pmdec": "pm_dec"}


def parse_gaia_name(gaia_name: str) -> tuple[int, int]:
    gaia_name_lower = gaia_name.lower().strip()
    if not gaia_name_lower.startswith("gaia dr"):
        raise KeyError(f"The given Gaia name is not of the format 'Gaia DR# #', see:{gaia_name}.")
    data_str = gaia_name_lower.replace("gaia dr", "")
    dr_number_str, id_number_str = data_str.split(" ")
    return int(dr_number_str), int(id_number_str)


def string_gaia_name(dr_number: int, id_number: int) -> str:
    return "Gaia DR" + str(dr_number) + " " + str(id_number)


def special_gaia_params(param_str: str, params_dicts, gaia_params_dict, param_names_found, gaia_ref, param_to_units):
    gaia_params_dict_keys = set(gaia_params_dict.keys())
    if 'dist' not in params_dicts.keys():
        params_dicts['dist'] = {}
    param_names_found.add('dist')
    main_value = gaia_params_dict[param_str]
    params_dicts['dist']['value'] = main_value
    params_dicts['dist']['ref'] = gaia_ref
    params_dicts['dist']['units'] = param_to_units[param_str]
    upper_key = f"{param_str}_upper"
    lower_key = f"{param_str}_lower"
    if upper_key in gaia_params_dict_keys:
        upper_error = gaia_params_dict[upper_key] - main_value
        del gaia_params_dict[upper_key]
    else:
        upper_error = None
    if lower_key in gaia_params_dict_keys:
        lower_error = gaia_params_dict[lower_key] - main_value
        del gaia_params_dict[lower_key]
    else:
        lower_error = None
    if lower_error is not None or upper_error is not None:
        params_dicts['dist']['err_low'] = lower_error
        params_dicts['dist']['err_high'] = upper_error
    del gaia_params_dict[param_str]
    return params_dicts


class GaiaLib:
    gaia_dr3_ref = gaia_dr3_ref

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.max_dr_number = 3
        self.dr_numbers = list(range(1, self.max_dr_number + 1))
        self.gaia_name_types = set()
        for dr_number in self.dr_numbers:
            self.gaia_name_types.add("gaia dr" + str(dr_number))
            self.__setattr__('gaiadr' + str(dr_number) + "_ref",
                             GaiaRef(verbose=self.verbose, dr_number=dr_number))
        self.gaia_query = GaiaQuery(verbose=self.verbose)

        self.object_params_to_trim = {"ra", "ra_error", 'dec', "dec_error", 'ref_epoch', "duplicated_source",
                                      "source_id"}

        self.special_case_params = {"r_est", "r_lo", 'r_hi',
                                    "teff_val", "teff_percentile_upper", 'teff_percentile_lower',
                                    "teff_gspphot", "teff_gspphot_upper", 'teff_gspphot_lower',
                                    'distance_gspphot', 'distance_gspphot_upper', 'distance_gspphot_lower',
                                    "distance_msc", "distance_msc_upper", 'distance_msc_lower',
                                    }

    def batch_update(self, dr_number, simbad_formatted_names_list):
        dr_number = int(dr_number)
        gaia_ref = self.__getattribute__('gaiadr' + str(dr_number) + "_ref")
        self.gaia_query.astroquery_source(simbad_formatted_name_list=simbad_formatted_names_list, dr_num=dr_number)
        gaia_star_ids = set(self.gaia_query.star_dict.keys())
        for gaia_star_id in gaia_star_ids:
            gaia_ref.add_ref({gaia_star_id}, self.gaia_query.star_dict[gaia_star_id])
        if gaia_star_ids != set():
            gaia_ref.save()

    def get_gaia_names_dict(self, star_name: str) -> tuple[str, dict[str, str]]:
        star_data_doc = get_star_data(star_name)
        attr_name = star_data_doc["attr_name"]
        available_gaia_name_types = set(star_data_doc.keys()) & self.gaia_name_types
        gaia_star_names_dict = {star_type: star_data_doc[star_type] for star_type in available_gaia_name_types}
        return attr_name, gaia_star_names_dict

    def get_single_dr_number_data(self, gaia_name):
        dr_number, gaia_star_id = parse_gaia_name(gaia_name)
        gaia_ref = self.__getattribute__('gaiadr' + str(dr_number) + "_ref")
        test_output = gaia_ref.find(gaia_star_id=gaia_star_id)
        if test_output is None:
            # is data available on the ESA website?
            self.gaia_query.astroquery_source([gaia_name], dr_num=dr_number)
            if gaia_star_id in self.gaia_query.star_dict.keys():
                # We found the data and can update the reference data so that it is found first next time
                gaia_params_dict = self.gaia_query.star_dict[gaia_star_id]
            else:
                # no data was found, we record this so that next time a search is not needed.
                gaia_params_dict = {}
            gaia_ref.add_ref({gaia_star_id}, gaia_params_dict)
            gaia_ref.save()
            gaia_ref.load()
            gaia_ref.make_lookup()
            # we try again to get the data, this time it should be found.
            return self.get_single_dr_number_data(gaia_name)
        # This is the default case, data is available in the reference file, and is returned
        return test_output

    def get_params_data(self, star_name: str) -> tuple[str, dict[str, any]]:
        attr_name, gaia_star_names_dict = self.get_gaia_names_dict(star_name=star_name)
        return attr_name, {gaia_name: self.get_single_dr_number_data(gaia_name)
                           for gaia_name in gaia_star_names_dict.values()}

    def convert_to_object_params(self, gaia_params_dicts):
        new_object_params = ObjectParams()
        for gaia_hypatia_name in gaia_params_dicts.keys():
            dr_number, _gaia_star_id = parse_gaia_name(gaia_hypatia_name)
            _gaia_ids, gaia_params_dict = gaia_params_dicts[gaia_hypatia_name]
            gaia_params_dict_keys = set(gaia_params_dict.keys())
            if dr_number == 3:
                ref_str = self.gaia_dr3_ref
            else:
                ref_str = "Gaia Data Release " + str(dr_number)
            params_dicts = {}
            param_names_found = set()
            # handling for the distance from the Bailer-Jones Catalog
            if "r_est" in gaia_params_dict_keys:
                params_dicts['dist'] = {}
                param_names_found.add('dist')
                params_dicts['dist']['value'] = gaia_params_dict["r_est"]
                params_dicts['dist']['ref'] = "Bailer-Jones et al. (2018)"
                params_dicts['dist']['units'] = self.gaia_query.param_to_units["r_est"]
                if "r_hi" in gaia_params_dict_keys:
                    upper_error = gaia_params_dict["r_hi"] - gaia_params_dict["r_est"]
                else:
                    upper_error = None
                if "r_lo" in gaia_params_dict_keys:
                    lower_error = gaia_params_dict["r_lo"] - gaia_params_dict["r_est"]
                else:
                    lower_error = None
                if lower_error is not None or upper_error is not None:
                    params_dicts['dist']['err_low'] = lower_error
                    params_dicts['dist']['err_high'] = upper_error
            if "distance_gspphot" in gaia_params_dict_keys:
                special_gaia_params("distance_gspphot", params_dicts, gaia_params_dict, param_names_found,
                                    self.gaia_dr3_ref, self.gaia_query.param_to_units)
            if "distance_msc" in gaia_params_dict_keys:
                special_gaia_params("distance_msc", params_dicts, gaia_params_dict, param_names_found,
                                    self.gaia_dr3_ref, self.gaia_query.param_to_units)
            if "teff_val" in gaia_params_dict_keys:
                params_dicts['teff'] = {}
                param_names_found.add('teff')
                params_dicts['teff']['value'] = gaia_params_dict["teff_val"]
                params_dicts['teff']['ref'] = ref_str
                params_dicts['teff']['units'] = self.gaia_query.param_to_units["teff_val"]
                if "teff_percentile_upper" in gaia_params_dict_keys:
                    upper_error = gaia_params_dict["teff_percentile_upper"] - gaia_params_dict["teff_val"]
                else:
                    upper_error = None
                if "teff_percentile_lower" in gaia_params_dict_keys:
                    lower_error = gaia_params_dict["teff_percentile_lower"] - gaia_params_dict["teff_val"]
                else:
                    lower_error = None
                if lower_error is not None or upper_error is not None:
                    params_dicts['teff']['err'] = (lower_error, upper_error)
            elif "teff_gspphot" in gaia_params_dict_keys:
                params_dicts['teff'] = {}
                param_names_found.add('teff')
                params_dicts['teff']['value'] = gaia_params_dict["teff_gspphot"]
                params_dicts['teff']['ref'] = ref_str
                params_dicts['teff']['units'] = self.gaia_query.param_to_units["teff_gspphot"]
                if "teff_gspphot_upper" in gaia_params_dict_keys:
                    upper_error = gaia_params_dict["teff_gspphot_upper"] - gaia_params_dict["teff_gspphot"]
                    del gaia_params_dict["teff_gspphot_upper"]
                else:
                    upper_error = None
                if "teff_gspphot_lower" in gaia_params_dict_keys:
                    lower_error = gaia_params_dict["teff_gspphot_lower"] - gaia_params_dict["teff_gspphot"]
                    del gaia_params_dict["teff_gspphot_lower"]
                else:
                    lower_error = None
                if lower_error is not None or upper_error is not None:
                    params_dicts['teff']['err_low'] = lower_error
                    params_dicts['teff']['err_high'] = upper_error
                del gaia_params_dict["teff_gspphot"]
            for param_key in gaia_params_dict_keys - self.special_case_params:
                if "_error" in param_key:
                    param_name = param_key.replace("_error", "")
                    if param_name not in param_names_found:
                        params_dicts[param_name] = {}
                        param_names_found.add(param_name)
                    params_dicts[param_name]['err_low'] = params_dicts[param_name]['err_high'] \
                        = gaia_params_dict[param_key]
                else:
                    if param_key not in param_names_found:
                        params_dicts[param_key] = {}
                        param_names_found.add(param_key)
                    params_dicts[param_key]['value'] = gaia_params_dict[param_key]
                    params_dicts[param_key]['ref'] = ref_str
                    if param_key in self.gaia_query.params_with_units:
                        params_dicts[param_key]['units'] = self.gaia_query.param_to_units[param_key]
            param_names = set(params_dicts.keys()) - self.object_params_to_trim
            for param_name in param_names:
                dict_this_param = params_dicts[param_name]
                if 'err' in dict_this_param.keys():
                    dict_this_param["err_low"], dict_this_param["err_high"] = dict_this_param["err"]
                    del dict_this_param["err"]
                param_name_lower = param_name.lower()
                if param_name_lower in rename_params.keys():
                    final_param_name = rename_params[param_name_lower]
                else:
                    final_param_name = param_name_lower
                new_object_params[final_param_name] = SingleParam.strict_format(param_name=final_param_name,
                                                                                **dict_this_param)
        return new_object_params

    def get_object_params(self, star_name: str):
        attr_name, gaia_params_dicts = self.get_params_data(star_name=star_name)
        return attr_name, self.convert_to_object_params(gaia_params_dicts=gaia_params_dicts)


class GaiaRef:
    def __init__(self, dr_number=2, verbose=False):
        self.dr_number = dr_number
        self.verbose = verbose
        self.ref_data = None
        self.gaia_name_type = "gaia dr" + str(self.dr_number)
        self.ref_file = os.path.join(ref_dir, "GaiaDR" + str(self.dr_number) + "_ref.csv")
        self.lookup = None
        self.available_ids = None

    def load(self):
        self.ref_data = []
        if os.path.exists(self.ref_file):
            read_ref = row_dict(filename=self.ref_file, key="name", delimiter=",", null_value="", inner_key_remove=True)
            for saved_names in read_ref.keys():
                star_ids = set()
                for simbad_formatted_gaia_name in saved_names.split("|"):
                    dr_number, gaia_star_id = parse_gaia_name(simbad_formatted_gaia_name)
                    star_ids.add(gaia_star_id)
                    if dr_number != self.dr_number:
                        raise KeyError(f"GaiaRef for data release {self.dr_number} " +
                                       f" received a Gaia name with the wrong release number: {simbad_formatted_gaia_name}.")
                self.ref_data.append((star_ids, read_ref[saved_names]))

    def save(self):
        self.make_lookup()
        header_params = set()
        name_string_to_params = {}
        for star_ids, params in self.ref_data:
            header_params |= set(params.keys())
            star_names_string = ""
            for star_id in star_ids:
                formatted_name = string_gaia_name(self.dr_number, star_id)
                star_names_string += formatted_name + "|"
            name_string_to_params[star_names_string[:-1]] = params
        header = "name,"
        sorted_header_params = sorted(header_params)
        for gaia_param in sorted_header_params:
            header += gaia_param + ","
        header = header[:-1] + "\n"
        body = []
        for output_string_name in sorted(name_string_to_params.keys()):
            params = name_string_to_params[output_string_name]
            row_data = output_string_name + ","
            params_this_row = set(params.keys())
            for param_name in sorted_header_params:
                if param_name in params_this_row:
                    row_data += str(params[param_name]) + ","
                else:
                    row_data += ","
            body.append(row_data[:-1] + "\n")
        with open(self.ref_file, 'w') as f:
            f.write(header)
            [f.write(row_data) for row_data in body]

    def add_ref(self, gaia_star_ids, params):
        if self.ref_data is None:
            self.load()
        self.ref_data.append((gaia_star_ids, params))

    def find(self, gaia_star_id):
        if self.lookup is None:
            self.make_lookup()
        if gaia_star_id in self.available_ids:
            return self.ref_data[self.lookup[gaia_star_id]]
        return None

    def make_lookup(self):
        if self.ref_data is None:
            self.load()
        self.lookup = {}
        self.available_ids = set()
        found_index = None
        for ref_index, (star_ids, params) in list(enumerate(self.ref_data)):
            for gaia_star_id in star_ids:
                if gaia_star_id not in self.available_ids:
                    self.available_ids.add(gaia_star_id)
                    self.lookup[gaia_star_id] = ref_index
                else:
                    found_index = self.lookup[gaia_star_id]
                    break
            if found_index is not None:
                # only add new types, do not overwrite
                print("Duplicate_data data found, removing duplicate and restarting the Gaia reference file tool:" +
                      " make_lookup")
                self.ref_data.pop(ref_index)
                # run this again with a duplicate entry removed.
                self.make_lookup()
                break





if __name__ == "__main__":
    gl = GaiaLib(verbose=True)
    hypatia_attr_name, gaia_params = gl.get_params_data(star_name="HD 1234")
    # gl.gaia_query.astroquery_source(simbad_formatted_name_list=["Gaia DR2 1016674048078637568",
    #                                                               "Gaia DR2 1076515002779544960"], dr_num=2)
