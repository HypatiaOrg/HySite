from hypatia.analyze.abund_cat import CatalogData
from hypatia.analyze.stats import ReducedAbundances
from hypatia.analyze.params import SingleStarParams
from hypatia.database.simbad.db import indexed_name_types
from hypatia.data_structures.object_params import ObjectParams, SingleParam

all_gaia_refs_ranked = ['Gaia DR3 Gaia Collaboration et al. (2016b) and Gaia Collaboration et al. (2022k)',
                        'Bailer-Jones et al. (2018)', 'Gaia Data Release 2', 'Gaia Data Release 1', ]
star_name_types = set(indexed_name_types)


def ref_rank_gaia(single_param: SingleParam):
    for i, ref_name in enumerate(all_gaia_refs_ranked):
        if ref_name == single_param.ref:
            return i
    else:
        raise ValueError(f"single_param.ref {single_param.ref} not in all_gaia_refs_ranked")


class SingleStar:
    def __init__(self, star_reference_name, simbad_doc, is_target=False, verbose=False):
        self.is_target = is_target
        self.verbose = verbose
        self.star_reference_name = star_reference_name
        self.simbad_doc = simbad_doc
        self.star_names = set(self.simbad_doc['aliases'])
        self.attr_name = self.simbad_doc['attr_name']
        self.available_star_name_types = set(self.simbad_doc.keys()) & star_name_types
        self.params = SingleStarParams()
        self.available_data_types = set()
        self.available_abundance_catalogs = set()
        self.catalog_to_norm_key = {}
        self.reduced_abundances = ReducedAbundances()
        self.exo = None

    def add_abundance_catalog(self, short_catalog_name, catalog_dict):
        self.__setattr__(short_catalog_name, CatalogData(catalog_dict))
        self.available_data_types.add(short_catalog_name)
        self.available_abundance_catalogs.add(short_catalog_name)

    def add_exoplanet_data(self, xo_data_this_star):
        self.exo = xo_data_this_star
        self.available_data_types.add("exo")

    def gaia_params(self, gaia_params_dicts):
        for param in sorted(gaia_params_dicts.keys()):
            singles_params_list = sorted(gaia_params_dicts[param], key=ref_rank_gaia)
            self.params.update_param(param_name=param, single_param=singles_params_list[0],
                                     overwrite_existing=True)

    def pastel_params(self, pastel_record):
        # Update so that existing parameter keys-value pairs are prioritized over new values.
        self.params.update_params(pastel_record, overwrite_existing=False)

    def xhip_params(self, xhip_params_dict: ObjectParams):
        self.params.update_params(xhip_params_dict, overwrite_existing=False)

    def reduce(self):
        for catalog in self.available_abundance_catalogs:
            for element_name in self.__getattribute__(catalog).available_abundances:
                abundance_value = self.__getattribute__(catalog).__getattribute__(element_name)
                self.reduced_abundances.add_abundance(abundance_value, element_name, catalog)
        self.reduced_abundances.calc()

    def find_thing(self, thing, type_of_thing):
        values = []
        if type_of_thing == "Stellar Parameter":
            if thing in self.params.available_params:
                values.append(self.params.__getattribute__(thing).value)
        elif type_of_thing == "Exoplanet Parameter":
            if "exo" in self.available_data_types:
                for planet_letter in self.exo.planet_letters:
                    single_planet = self.exo.__getattribute__(planet_letter)
                    if thing in single_planet.planet_params:
                        values.append(single_planet.__getattribute__(thing))
        elif type_of_thing == "Stellar Abundance":
            for catalog_name in self.available_abundance_catalogs:
                available_abundances = self.__getattribute__(catalog_name).available_abundances
                if thing in available_abundances:
                    value = self.__getattribute__(catalog_name).__getattribute__(thing)
                    values.append(value)
        return values
