import numpy as np

from hypatia.object_params import params_err_format
from hypatia.elements import get_representative_error, ElementID


class ElementStats:
    def __init__(self, element_name: ElementID | str):
        self.name = element_name
        if isinstance(element_name, ElementID):
            self.element_id = element_name
        else:
            self.element_id = ElementID.from_str(element_name)
        self.value_list = []
        self.catalog_list = []
        self.catalogs = {}
        self.len = 0
        self.mean = self.median = self.max = self.min = self.spread = self.plusminus = self.std = None

    def add_value(self, value: float, catalog: str):
        formatted_value = np.around(float(value), decimals=3)
        self.value_list.append(formatted_value)
        self.catalog_list.append(catalog)
        self.catalogs[catalog] = formatted_value

    def calc_stats(self):
        self.len = self.__len__()
        if self.len < 1:
            pass
        elif self.len < 2:
            self.mean = self.median = self.max = self.min = self.value_list[0]
        else:
            self.mean = np.around(np.mean(self.value_list), decimals=3)
            self.median = np.around(np.median(self.value_list), decimals=3)
            self.max = np.max(self.value_list)
            self.min = np.min(self.value_list)
            self.spread = np.around(self.max - self.min, decimals=3)
            self.plusminus = np.around(self.spread / 2.0, decimals=2)
            if self.len > 2:
                self.std = params_err_format(np.std(self.value_list), sig_figs=3)
        if self.plusminus is None or self.plusminus == 0.0:
            self.plusminus = get_representative_error(element_name=self.name)

    def __len__(self):
        return len(self.value_list)

    def __getitem__(self, item):
        return self.__getattribute__(item)


class ReducedAbundances:
    def __init__(self):
        self.available_abundances = set()

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def add_abundance(self, abundance_record, element_name, catalog):
        if element_name not in self.available_abundances:
            self.__setattr__(element_name, ElementStats(element_name))
            self.available_abundances.add(element_name)
        self.__getattribute__(element_name).add_value(abundance_record, catalog)

    def calc(self):
        [self.__getattribute__(element_name).calc_stats() for element_name in self.available_abundances]
