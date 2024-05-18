import os

from hypatia.config import ref_dir
from hypatia.tools.table_read import row_dict
from hypatia.data_structures.object_params import ObjectParams, SingleParam


class Xhip:
    xhip_params = {"RAJ2000", "DECJ2000", "Plx", "e_Plx", "pmRA", "pmDE", "GLon", "Glat", "Dist", "X",
                   "Y", "Z", "SpType", "RV", "U", "V", "W", "Bmag", "Vmag", "TWOMASS", "Lum", "rSpType", "BV"}
    rename_dict = {"X": "X_pos", "Y": "Y_pos", "Z": "Z_pos", "U": "U_vel", "V": "V_vel", "W": "W_vel"}

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

    def get_xhip_data(self, hip_name: str) -> ObjectParams or None:
        hip_number_str = hip_name.lower().split("hip")[1].strip()
        if hip_number_str[-1].lower() == 'a':
            hip_number_str = hip_number_str[:-1].strip()
        try:
            hip_number = int(hip_number_str)
        except ValueError:
            return None
        if hip_number in self.available_hip_names:
            xhip_params_dict_before_rename = {param: self.ref_data[hip_number][param]
                                              for param in self.xhip_params
                                              if param in self.ref_data[hip_number].keys()}
            xhip_params_dict = ObjectParams()
            rename_keys = set(self.rename_dict.keys())
            for param_name in xhip_params_dict_before_rename:
                single_param = SingleParam(value=xhip_params_dict_before_rename[param_name], ref='xhip')
                if param_name in rename_keys:
                    xhip_params_dict[self.rename_dict[param_name]] = single_param
                else:
                    xhip_params_dict[param_name] = single_param
            # Update in this way so that existing parameter keys-value pairs are prioritized over new values.
            return xhip_params_dict
        return None


if __name__ == "__main__":
    xhip = Xhip(auto_load=True)