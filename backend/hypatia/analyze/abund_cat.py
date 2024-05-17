class CatalogData:
    def __init__(self, catalog_dict):
        self.original_catalog_star_name = catalog_dict["original_star_name"]
        self.main_star_id = catalog_dict["main_id"]
        self.original_catalog_norm = catalog_dict["norm_key"]
        self.catalog_long_name = catalog_dict["long_name"]
        self.available_abundances = set()
        for element in set(catalog_dict.keys()) - {"star_name", "norm_key", "long_name"}:
            self.__setattr__(element, catalog_dict[element])
            self.available_abundances.add(element)
        self.normalization = None
        self.elements_that_can_not_be_normalized = None

    def normalize(self, norm_dict, norm_key):
        if self.normalization is not None:
            raise UnboundLocalError("The data is not allowed to be normalized twice, this is because some data is " +
                                    "removed during a normalization. Reinitialize to do this normalization.")
        self.elements_that_can_not_be_normalized = set()
        if norm_key == "original":
            self.normalization = (self.original_catalog_norm, norm_dict[self.original_catalog_norm])
        else:
            self.normalization = (norm_key, norm_dict[norm_key])
        normalization_element_keys = set(self.normalization[1].keys())
        overlapping_elements = self.available_abundances & normalization_element_keys
        for element in overlapping_elements:
            # the normalization, it is a bit anti-climatic.
            self.__setattr__(element, self.__getattribute__(element) - self.normalization[1][element])
        # deal with the elements that could not be normalized.
        for not_normalized_element in self.available_abundances - normalization_element_keys:
            self.__delattr__(not_normalized_element)
            self.available_abundances.remove(not_normalized_element)
            self.elements_that_can_not_be_normalized.add(not_normalized_element)
