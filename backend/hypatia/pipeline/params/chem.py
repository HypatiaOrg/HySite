import numpy as np

from hypatia.object_params import params_err_format
from hypatia.elements import get_representative_error, ElementID


class ElementStats:
    def __init__(self, element_name: ElementID | str):
        self.name = element_name
        self.element_id = element_name
        self.value_list = []
        self.value_list_linear = []
        self.catalog_list = []
        self.catalogs = {}
        self.catalogs_linear = {}
        self.len = 0
        self.mean = self.median = self.max = self.min = self.spread = self.plusminus = self.std = self.median_catalogs = None

    def add_value(self, value: float, catalog: str):
        value = float(value)
        formatted_value = np.around(value, decimals=3)
        value_linear = 10.0**(formatted_value)
        self.value_list.append(formatted_value)
        self.value_list_linear.append(value_linear)
        self.catalog_list.append(catalog)
        self.catalogs[catalog] = formatted_value
        self.catalogs_linear[catalog] = value_linear

    def calc_stats(self):
        self.len = self.__len__()
        if self.len < 1:
            pass
        elif self.len < 2:
            self.mean = self.median = self.max = self.min = np.around(self.value_list[0], decimals=2)
            self.median_catalogs = [self.catalog_list[0]]
        else:
            value_array = np.array(self.value_list)
            self.mean = np.around(np.log10(np.mean(np.array(self.value_list_linear))), decimals=2)
            self.median = np.around(np.median(value_array), decimals=2)
            self.max = np.max(value_array)
            self.min = np.min(value_array)
            self.spread = np.around(self.max - self.min, decimals=3)
            self.plusminus = np.around(self.spread / 2.0, decimals=2)
            value_list_sorted, catalog_list_sorted = zip(*sorted(zip(self.value_list, self.catalog_list)))
            half_index, remainder = divmod(len(value_list_sorted), 2)
            if remainder == 0:
                median_slice = slice(half_index - 1, half_index + 1)
            else:
                median_slice = slice(half_index, half_index + 1)
            self.median_catalogs = catalog_list_sorted[median_slice]
            if self.len > 2:
                self.std = params_err_format(np.std(self.value_list), sig_figs=3)
        if self.plusminus is None or self.plusminus == 0.0:
            self.plusminus = get_representative_error(element_id=self.element_id)

    def __len__(self):
        return len(self.value_list)

    def __getitem__(self, item):
        return self.__getattribute__(item)


class ReducedAbundances:
    def __init__(self):
        self.available_abundances = set()

    def __getitem__(self, item):
        return self.__getattribute__(str(item))

    def add_abundance(self, abundance_record, element_name, catalog):
        if element_name not in self.available_abundances:
            self.__setattr__(str(element_name), ElementStats(element_name))
            self.available_abundances.add(element_name)
        self.__getattribute__(str(element_name)).add_value(abundance_record, catalog)

    def calc(self):
        [self.__getattribute__(str(element_name)).calc_stats() for element_name in self.available_abundances]
