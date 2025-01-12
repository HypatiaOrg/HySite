import os

from hypatia.config import ref_dir
from hypatia.tools.table_read import row_dict
from hypatia.elements import spectral_type_to_float
from hypatia.object_params import ObjectParams, SingleParam


class Xhip:
    xhip_params = {"RAJ2000", "DECJ2000", "Plx", "e_Plx", "pmRA", "pmDE", "GLon", "Glat", "Dist", "X",
                   "Y", "Z", "SpType", "RV", "U", "V", "W", "Bmag", "Vmag", "Lum", "rSpType", "BV"}
    rename_dict = {"X": "x_pos", "Y": "y_pos", "Z": "z_pos", "U": "u_vel", "V": "v_vel", "W": "w_vel",
                   'RV': 'radial_velocity', 'Plx': 'parallax', 'e_Plx': 'parallax_err',
                   "pmRA": "pm_ra", "pmDE": "pm_dec",}
    xhip_units = {"RAJ2000": "deg", "DECJ2000": "deg", "Plx": "mas", "e_Plx": "mas", "pmRA": "mas/yr",
                  "pmDE": "mas/yr", "GLon": "deg", "Glat": "deg", "Dist": "[pc]", "X": "[pc]", "Y": "[pc]",
                  "Z": "[pc]", "SpType": "string", "RV": "km/s", "U": "km/s", "V": "km/s", "W": "km/s", "Bmag": "mag",
                  "Vmag": "mag", "Lum": "L_sun", "rSpType": "string", "BV": "mag"}

    def __init__(self, auto_load=False):
        self.xhip_file_name = os.path.join(ref_dir, "xhip.csv")
        self.ref_data = None
        self.comments = None
        self.available_hip_names = None
        if auto_load:
            self.load()

    def load(self, verbose: bool = False):
        """
        X Hip - it has two types of null values 99.99 and ''
        """
        if verbose:
            print("    Loading XHip data")
        raw_data = row_dict(self.xhip_file_name, key='HIP', delimiter=",", null_value=99.99)
        if "comments" in raw_data.keys():
            self.comments = raw_data['comments']
            del raw_data['comments']
        self.ref_data = {xhip_key: {param_key: raw_data[xhip_key][param_key] for param_key in raw_data[xhip_key].keys()
                                    if raw_data[xhip_key][param_key] != ""} for xhip_key in raw_data.keys()}
        if self.comments is not None:
            self.ref_data["comments"] = self.comments
        self.available_hip_names = set(self.ref_data.keys())
        if verbose:
            print("    XHip data loaded")

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
            parallax_err = None
            if 'e_Plx' in xhip_params_dict_before_rename.keys():
                parallax_err = xhip_params_dict_before_rename['e_Plx']
                del xhip_params_dict_before_rename['e_Plx']
            base_ref = f"XHip Catalog (HIP {hip_number})"
            for param_name in xhip_params_dict_before_rename:
                err_low = None
                err_high = None
                ref = base_ref
                if "rSpType" == param_name:
                    # This is the reference for the spectral type
                    continue
                elif 'Plx' == param_name:
                    if parallax_err is not None:
                        err_high = abs(parallax_err)
                        err_low = -err_high
                elif param_name == 'SpType' and 'rSpType' in xhip_params_dict_before_rename.keys():
                    ref += f": {xhip_params_dict_before_rename['rSpType']}"
                if param_name in rename_keys:
                    param_key = self.rename_dict[param_name]
                else:
                    param_key = param_name
                value = xhip_params_dict_before_rename[param_name]
                units = self.xhip_units[param_name]
                xhip_params_dict[param_key] = SingleParam.strict_format(
                    param_name=param_key,
                    value=value,
                    ref=ref,
                    units=units,
                    err_low=err_low,
                    err_high=err_high)
                if param_key.lower() == 'sptype':
                    xhip_params_dict['sptype_num'] = SingleParam.strict_format(param_name='sptype_num',
                        value=spectral_type_to_float(value), ref=ref, units='')
            # Update in this way so that existing parameter keys-value pairs are prioritized over new values.
            return xhip_params_dict
        return None


if __name__ == "__main__":
    xhip = Xhip(auto_load=True)