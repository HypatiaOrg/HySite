import os
from warnings import warn

import requests

from hypatia.tools.table_read import row_dict
from hypatia.configs.env_load import MONGO_DATABASE
from hypatia.pipeline.summary import SummaryCollection
from hypatia.tools.color_text import attention_yellow_text
from hypatia.configs.file_paths import solar_norm_ref, summary_api_url
from hypatia.elements import summary_dict, element_rank, ElementID, iron_id, iron_ii_id


iron_set = {iron_id, iron_ii_id}
element_abrevs = set(summary_dict.keys())


def un_norm_x_over_h(relative_x_over_h: float, solar_x: float):
    """
    We take the relative value of an element X to Hydrogen (H) of a star compared to the solar abundance of the same
    ratio. Note that this calculation takes place in Log base 10 space, and returns values in log space, so simple
    additions and subtractions are all that is necessary for this calculation.

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
    if test_ratio_lower.endswith('a'):
        un_norm_func_name = 'un_norm_abs_x'
        element_string = test_ratio[:-1]
    elif test_ratio_lower.endswith('h'):
        element_string = test_ratio[:-1]
        un_norm_func_name = 'un_norm_x_over_h'
    elif test_ratio_lower.endswith('fe'):
        element_string = test_ratio[:-2]
        un_norm_func_name = 'un_norm_x_over_fe'
    else:
        raise KeyError(f'The Abundance: {test_ratio} is not of the expected formats.')
    element_record = ElementID.from_str(element_string=element_string.strip('_'))
    return element_record, un_norm_func_name


class SolarNorm:
    ref_columns = {'author', 'year'}

    def __init__(self, file_path: str | os.PathLike | None = None, verbose: bool = True):
        if file_path is None:
            file_path = solar_norm_ref
        self.verbose = verbose
        self.file_path = file_path
        if os.path.exists(file_path):
            norm_data = row_dict(self.file_path, key='catalog', delimiter=',', null_value='')
            self.comments = norm_data.pop('comments')
            self.solar_norm_dict = {cat_name: {ElementID.from_str(element_string=el_str): float(el_val)
                                               for el_str, el_val in cat_data.items() if el_str not in self.ref_columns}
                                    for cat_name, cat_data in norm_data.items()}
            self.ref_data = {cat_name: {ref_type: cat_data[ref_type] for ref_type in self.ref_columns}
                             for cat_name, cat_data in norm_data.items()}
        else:
            self.comments = None
            print(f'Solar Norm file: {file_path} does not exist')
            self.solar_norm_dict = {}
            self.ref_data = {}
            summary_db = SummaryCollection(db_name=MONGO_DATABASE, collection_name='summary')
            if summary_db.collection_exists():
                print(f'  Loading Solar Norm from the database')
                summary_data = summary_db.find_one()
                norm_data = summary_data['normalizations']
            else:
                print('  ' + attention_yellow_text(f'Downloading the file from: {summary_api_url}'))
                response = requests.get(summary_api_url)
                if response.status_code == 200:
                    norm_data = response.json()
                else:
                    warn(f'Failed to download the Solar Norm file from: {summary_api_url}, using an empty dictionary!')
                    norm_data = {}
            for cat_name, cat_data in norm_data.items():
                try:
                    self.solar_norm_dict[cat_name] = cat_data.pop('values')
                except KeyError:
                    # this happens for the 'original' and 'absolute' keys
                    pass
                else:
                    self.ref_data[cat_name] = {key_name: cat_data[key_name] for key_name in cat_data.keys()
                                               if key_name in self.ref_columns}

        if self.verbose:
            print('Solar Norm data loaded.')

    def __call__(self, norm_key=None):
        if norm_key is None:
            return self.solar_norm_dict
        if norm_key.lower() == 'absolute':
            return None
        else:
            return self.solar_norm_dict[norm_key.lower()]

    def add_normalization(self, handle: str, author:str, year: int | str, element_dict: dict[str | ElementID, float]):
        formated_dict = {}
        for el_name, solar_values in element_dict.items():
            if isinstance(el_name, ElementID):
                formated_dict[el_name] = solar_values
            else:
                formated_dict[ElementID.from_str(el_name)] = solar_values
        self.solar_norm_dict[handle] = formated_dict
        self.ref_data[handle] = {'author': author, 'year': year}

    def write(self, write_file=None):
        if write_file is None:
            write_file = self.file_path

        norm_keys = self.solar_norm_dict.keys()
        element_keys = set()
        [element_keys.add(element) for norm_key in norm_keys for element in self.solar_norm_dict[norm_key].keys()
         if element not in self.ref_columns]
        sorted_element_records = sorted(element_keys,  key=element_rank)
        sorted_header_keys = ['catalog'] + list(sorted(self.ref_columns)) + sorted_element_records
        header = ','.join([str(column_name) for column_name in sorted_header_keys]) + '\n'
        body = ''
        for norm_key in sorted(norm_keys):
            values_dict = self.solar_norm_dict[norm_key] | self.ref_data[norm_key] | {'catalog': norm_key}
            values_list = [str(values_dict[header_key]) if header_key in values_dict.keys() else ''
                           for header_key in sorted_header_keys]
            body += ','.join(values_list) + '\n'
        with open(write_file, 'w') as f:
            if self.comments is not None:
                for comment in self.comments:
                    f.write('# ' + comment + '\n')
            f.write(header)
            f.write(body)

    def to_record(self, norm_keys: list[str] = None) -> dict[str, dict[str, str | int | dict[str, float]]]:
        if norm_keys is None:
            norm_keys = list(self.solar_norm_dict.keys())
        if 'original' in norm_keys:
            norm_keys.remove('original')
        if 'absolute' in norm_keys:
            norm_keys.remove('absolute')
        return {norm_key: {**self.ref_data[norm_key], 'values': {str(el_id): self.solar_norm_dict[norm_key][el_id]
                                                                 for el_id in sorted(self.solar_norm_dict[norm_key].keys(),
                                                                                     key=element_rank)},
                           'notes': f'This key provides data that is normalized to the Sun using values from {self.ref_data[norm_key]["author"]}'}
                for norm_key in norm_keys}


solar_norm = SolarNorm()
solar_norm_dict = solar_norm()

if __name__ == '__main__':
    # solar_norm.write(os.path.join(ref_dir, 'test_solar_norm.csv'))
    pass
