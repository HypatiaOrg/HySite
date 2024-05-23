import numpy as np

from hypatia.sources.catalogs.solar import solar_norm_dict


class SingleNorm:
    def __init__(self, norm_key: str, norm_data: dict[str, float]):
        self.norm_key = norm_key
        self.available_abundances = set(norm_data.keys())
        for element, value in norm_data.items():
            self.__setattr__(element, value)

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def __contains__(self, item):
        return item in self.available_abundances


class CatalogData:
    non_element_keys = {"star_name", "norm_key", "long_name", "original_star_name", "main_id"}

    def __init__(self, catalog_dict):
        self.original_catalog_star_name = catalog_dict["original_star_name"]
        self.main_star_id = catalog_dict["main_id"]
        self.original_catalog_norm = catalog_dict["norm_key"]
        self.catalog_long_name = catalog_dict["long_name"]
        self.available_abundances = set()
        for element in set(catalog_dict.keys()) - self.non_element_keys:
            self.__setattr__(element, catalog_dict[element])
            self.available_abundances.add(element)
        self.normalizations = set()

    def normalize(self, norm_key):
        if norm_key == "original":
            norm_to_use = self.original_catalog_norm
        else:
            norm_to_use = norm_key
        elements_dict = solar_norm_dict[norm_to_use]
        overlapping_elements = self.available_abundances & set(elements_dict.keys())
        if overlapping_elements:
            norm_data = {element: np.around(self.__getattribute__(element) - elements_dict[element], decimals=3)
                         for element in overlapping_elements}
            self.__setattr__(norm_key, SingleNorm(norm_key, norm_data))
            self.normalizations.add(norm_key)
