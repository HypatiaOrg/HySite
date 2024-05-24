import os

from hypatia.config import ref_dir
from hypatia.tools.table_read import row_dict
from hypatia.sources.catalogs.norm import un_norm_functions
from hypatia.elements import summary_dict, element_rank, ElementID

element_abrevs = set(summary_dict.keys())


def ratio_to_element(test_ratio: str) -> tuple[ElementID, str]:
    test_ratio = test_ratio.strip().replace(' ', '_')
    test_ratio_lower = test_ratio.lower()
    if test_ratio_lower.endswith("a"):
        un_norm_func_name = "un_norm_abs_x"
        element_string = test_ratio[:-1]
    elif test_ratio_lower.endswith("h"):
        element_string = test_ratio[:-1]
        un_norm_func_name = "un_norm_x_over_h"
    elif test_ratio_lower.endswith("fe"):
        element_string = test_ratio[:-2]
        un_norm_func_name = "un_norm_x_over_fe"
    else:
        raise KeyError(f"The Abundance: {test_ratio} is not of the expected formats.")
    element_record = ElementID.from_str(element_string=element_string.strip('_'))
    return element_record, un_norm_func_name


iron_id = ElementID.from_str("Fe")


def un_norm(element_dict, norm_dict, element_id_to_un_norm_func):
    un_norm_dict = {}
    key_set = set(element_dict.keys())
    for element_id in key_set:
        un_norm_func_name = element_id_to_un_norm_func[element_id]
        if un_norm_func_name == "un_norm_x_over_fe":
            if element_id in norm_dict.keys():
                un_norm_dict[element_id] = un_norm_functions[un_norm_func_name](element_dict[element_id],
                                                                                element_dict[iron_id],
                                                                                norm_dict[element_id])
        elif un_norm_func_name == "un_norm_x_over_h":
            if element_id in norm_dict.keys():
                un_norm_dict[element_id] = un_norm_functions[un_norm_func_name](element_dict[element_id],
                                                                                norm_dict[element_id])
        else:
            un_norm_dict[element_id] = un_norm_functions[un_norm_func_name](element_dict[element_id])
    return un_norm_dict


class SolarNorm:
    ref_column = "#ref"

    def __init__(self, file_path=None):
        if file_path is None:
            file_path = os.path.join(ref_dir, "solar_norm_ref.csv")
        self.file_path = file_path
        self.sol_abund = {cat_name: {ElementID.from_str(element_string=el_str): float(el_val)
                                     for el_str, el_val in cat_data.items() if el_str != self.ref_column}
                          for cat_name, cat_data in
                          row_dict(self.file_path, key="catalog", delimiter=",", null_value="").items()}

    def __call__(self, norm_key=None):
        if norm_key is None:
            return self.sol_abund
        if norm_key.lower() == "absolute":
            return None
        else:
            return self.sol_abund[norm_key.lower()]

    def add_normalization(self, handle, element_dict):
        self.sol_abund[handle] = element_dict

    def write(self, write_file=None):
        if write_file is None:
            write_file = self.file_path

        norm_keys = self.sol_abund.keys()
        element_keys = set()
        [element_keys.add(element) for norm_key in norm_keys for element in self.sol_abund[norm_key].keys()
         if element != self.ref_column]
        sorted_element_records = sorted([ElementID.from_str(element_string=el_str) for el_str in element_keys],
                                        key=element_rank)
        sorted_element_keys = ['catalog'] + [str(el_rec) for el_rec in sorted_element_records] + [self.ref_column]
        header = ','.join(sorted_element_keys)
        body = ''
        for norm_key in sorted(norm_keys):
            self.sol_abund[norm_key]['catalog'] = norm_key
            element_keys_this_dict = set(self.sol_abund[norm_key].keys())
            for header_key in sorted_element_keys:
                if header_key in element_keys_this_dict:
                    body += str(self.sol_abund[norm_key][header_key]) + ','
                else:
                    body += ","
            body = body[:-1] + '\n'
        with open(write_file, 'w') as f:
            f.write(header)
            f.write(body)


sn = SolarNorm()
solar_norm_dict = sn()

if __name__ == "__main__":
    # sn.write(os.path.join(ref_dir, "test_solar_norm.csv"))
    pass
