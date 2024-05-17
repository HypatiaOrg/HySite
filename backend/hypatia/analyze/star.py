from hypatia.analyze.abund_cat import CatalogData
from hypatia.database.simbad.ops import get_attr_name
from hypatia.analyze.stats import ReducedAbundances
from hypatia.analyze.params import SingleStarParams
from hypatia.data_structures.object_params import ObjectParams, SingleParam

all_gaia_refs_ranked = ['Gaia DR3 Gaia Collaboration et al. (2016b) and Gaia Collaboration et al. (2022k)',
                        'Bailer-Jones et al. (2018)', 'Gaia Data Release 2', 'Gaia Data Release 1', ]


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

    def pastel_params(self, pastel_name_types, pastel, requested_pastel_params):
        found_names = {}
        names_this_star = set(self.star_names)
        for star_name in names_this_star:
            for pastel_name_type in pastel_name_types:
                if star_name.lower().startswith(pastel_name_type):
                    if not (star_name[0] == "*" and star_name[1] == "*"):
                        found_names[pastel_name_type] = star_name
                        break

        for this_star_name_type, this_star_name in found_names.items():
            if this_star_name in pastel.pastel_star_names[this_star_name_type]:
                found_params = requested_pastel_params & \
                               set(pastel.pastel_ave[this_star_name_type][this_star_name].keys())
                pastel_params_dict = ObjectParams({param: SingleParam(value=pastel.pastel_ave[this_star_name_type][this_star_name][param], ref='Pastel')
                                                   for param in found_params})
                # Update so that existing parameter keys-value pairs are prioritized over new values.
                self.params.update_params(pastel_params_dict, overwrite_existing=False)
                """
                No need to keep searching, there will only be star_type, star_id combination for the pastel 
                reference data.
                """
                break

    def xhip_params(self, xhip, available_xhip_ids, xhip_params, rename_dict):
        if "hip" in self.available_star_name_types:
            for hip_star_id in self.simbad_doc["hip"]:
                hip_number = hip_star_id[0]
                """
                    xhip - there are some missing values in this catalog
                """
                if hip_number in available_xhip_ids:
                    xhip_params_dict_before_rename = {param: xhip.ref_data[hip_number][param]
                                                      for param in xhip_params
                                                      if param in xhip.ref_data[hip_number].keys()}
                    xhip_params_dict = ObjectParams()
                    rename_keys = set(rename_dict.keys())
                    for param_name in xhip_params_dict_before_rename:
                        single_param = SingleParam(value=xhip_params_dict_before_rename[param_name], ref='xhip')
                        if param_name in rename_keys:
                            xhip_params_dict[rename_dict[param_name]] = single_param
                        else:
                            xhip_params_dict[param_name] = single_param
                    # Update in this way so that existing parameter keys-value pairs are prioritized over new values.
                    self.params.update_params(xhip_params_dict, overwrite_existing=True)

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
