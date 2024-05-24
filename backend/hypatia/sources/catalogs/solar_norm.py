import os

from hypatia.config import ref_dir
from hypatia.tools.table_read import row_dict
from hypatia.elements import summary_dict, element_rank, ElementID

iron_id = ElementID.from_str("Fe")
iron_ii_id = ElementID.from_str("Fe_II")
iron_set = {iron_id, iron_ii_id}
element_abrevs = set(summary_dict.keys())


def un_norm_x_over_h(relative_x_over_h: float, solar_x: float):
    """
    We take the relative value of an element X to Hydrogen (H) of a star compared to the solar abundance of the same
    ratio. Note that this calculation takes place in Log base 10 space, and returns values in log space, so simple
    additions and subtractions are all that is needed for this calculation.

    The abundance of Hydrogen, H_star, is defined as 10^12 atoms thus log(H_star) = log(10^12) = 12. By this definition,
    H_solar := log(10^12) = 12 and H_star := log(10^12) = 12 thus H_star = H_solar

    All other abundances are compared to that value. For a given elements X if may hav 10^6 atoms per 10^12 hydrogen
    atoms. Thus, the absolute abundance of element X is reported as log(X_star) = log(10^6) = 6. Since Hydrogen is the
    most abundant element for any star each the reported elemental abundance will be in the range of
    [12, -inf] = [log(10^12), log(0)].

    :param relative_x_over_h: is equal to log(X_star / H_star) - log(X_solar / H_solar)
                                        = log(X_star) - log(H_star) - log(X_solar) + log(H_solar)
        but since H_solar = H_star by definitions we have:
                      relative_x_over_h = log(X_star) - log(X_solar)
    :param solar_x: id equal to log(X_solar)
    :return: log(X_star) = relative_x_over_h + log(solar) = log(X_star) - log(X_solar) + log(X_solar)
    """
    return relative_x_over_h + solar_x


def un_norm_x_over_fe(relative_x_over_fe: float, relative_fe_over_h: float, solar_x: float):
    """
    We take the relative value of an element X to Iron (Fe) of a star compared to the solar abundance of the same
    ratio. Note that this calculation takes place in Log base 10 space, and returns values in log space, so simple
    additions and subtractions are all that is needed for this calculation.

    The abundance of Hydrogen, H_star, is defined as 10^12 atoms thus log(H_star) = log(10^12) = 12. By this definition,
    H_solar := log(10^12) = 12 and H_star := log(10^12) = 12 thus H_star = H_solar

    All other abundances are compared to that value. For a given elements X if may hav 10^6 atoms per 10^12 hydrogen
    atoms. Thus, the absolute abundance of element X is reported as log(X_star) = log(10^6) = 6. Since Hydrogen is the
    most abundant element for any star each the reported elemental abundance will be in the range of
    [12, -inf] = [log(10^12), log(0)].

    We calculate the intermediate product log(X_relative / H_relative) = log(X_star / H_star) - log(X_solar / H_solar)
    as: relative_x_over_fe + relative_fe_over_h = log(X_relative / Fe_relative) + log(Fe_relative / H_relative)
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star / Fe_star) - log(X_solar / Fe_solar)
                                                        + log(Fe_star/ H_star) - log(Fe_solar / H_solar)
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star * Fe_solar / (Fe_star * X_solar))
                                                        + log(Fe_star * H_solar / (H_star * Fe_solar))
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star * Fe_solar * Fe_star * H_solar
                                                        / (Fe_star * X_solar * H_star * Fe_solar))
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star * H_solar / (X_solar * H_star))
    <=> relative_x_over_fe + relative_fe_over_h = log(X_star / H_star) - log(X_solar / H_solar)
    <=> relative_x_over_fe + relative_fe_over_h = log(X_relative / H_relative)
    which we name relative_x_over_h as log(X_relative / H_relative) = relative_x_over_fe + relative_fe_over_h

    At this point we have the case that handled by the function un_norm_x_over_h defined above to return the
    desired log(X_star / H_star) = un_norm_x_over_h(relative_x_over_h, solar_x_over_h)

    :param relative_x_over_fe: log(X_relative / Fe_relative) = log(X_star / Fe_star) - log(X_solar / Fe_solar)
    :param relative_fe_over_h: log(Fe_relative / H_relative) = log(Fe_star/ H_star) - log(Fe_solar / H_solar)
    :param solar_x: log(X_solar)
    :return: log(X_star)
    """
    relative_x_over_h = relative_x_over_fe + relative_fe_over_h
    return un_norm_x_over_h(relative_x_over_h, solar_x)


def un_norm_abs_x(absolute_x: float):
    """
    Absolute data is already in the desired standard. Nothing is is done here for to un normalize the data.

    The abundance of Hydrogen, H_star, is defined as 10^12 atoms thus log(H_star) = log(10^12) = 12. By this definition,
    H_solar := log(10^12) = 12 and H_star := log(10^12) = 12 thus H_star = H_solar

    All other abundances are compared to that value. For a given elements X if may hav 10^6 atoms per 10^12 hydrogen
    atoms. Thus, the absolute abundance of element X is reported as log(X_star) = log(10^6) = 6. Since Hydrogen is the
    most abundant element for any star each the reported elemental abundance will be in the range of
    [12, -inf] = [log(10^12), log(0)].

    :param absolute_x: is equal to log(X_star)
    :return: absolute_x = log(X_star)
    """
    return absolute_x


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
