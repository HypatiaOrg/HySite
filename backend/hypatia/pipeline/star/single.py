from operator import attrgetter

from hypatia.object_params import param_to_units
from hypatia.pipeline.abund_cat import CatalogData
from hypatia.elements import spectral_type_to_float
from hypatia.sources.simbad.db import indexed_name_types
from hypatia.pipeline.params.star import SingleStarParams
from hypatia.pipeline.params.chem import ReducedAbundances
from hypatia.object_params import ObjectParams, SingleParam


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
        self.reduced_abundances = {'absolute': ReducedAbundances()}
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
            for single_param in singles_params_list:
                self.params.update_param(param_name=param, single_param=single_param, overwrite_existing=False)

    def pastel_params(self, pastel_record: ObjectParams):
        # Update so that existing parameter keys-value pairs are prioritized over new values.
        self.params.update_params(pastel_record, overwrite_existing=False)

    def exo_params(self):
        if "exo" in self.available_data_types:
            exo_stellar_data = self.exo.get('stellar', None)
            if exo_stellar_data is not None:
                for param, values_set in exo_stellar_data.items():
                    for single_param in sorted(values_set, key=attrgetter('ref'), reverse=True):
                        self.params.update_param(param_name=param, single_param=single_param, overwrite_existing=False)

    def xhip_params(self, xhip_params_dict: ObjectParams):
        self.params.update_params(xhip_params_dict, overwrite_existing=False)

    def simbad_params(self, overwrite_existing=False):
        simbad_doc = self.simbad_doc
        # coordinate parameters
        raj2000 = simbad_doc.get('ra', None)
        decj2000 = simbad_doc.get('dec', None)
        hmsdms = simbad_doc.get('hmsdms', None)
        coord_bibcode = simbad_doc.get('coord_bibcode', None)
        truth_array = [
            raj2000 is not None,
            decj2000 is not None,
            hmsdms is not None,
            coord_bibcode is not None,
        ]
        if all(truth_array):
            ref = f'SIMBAD provided bibcode: {coord_bibcode}'
            ra_param = SingleParam.strict_format(param_name='raj2000', value=raj2000, ref=ref, units='deg')
            dec_param = SingleParam.strict_format(param_name='decj2000', value=decj2000, ref=ref, units='deg')
            hmsdms_param = SingleParam.strict_format(param_name='hmsdms', value=hmsdms, ref=ref, units='string')
            self.params.update_param(param_name='raj2000', single_param=ra_param, overwrite_existing=overwrite_existing)
            self.params.update_param(param_name='decj2000', single_param=dec_param, overwrite_existing=overwrite_existing)
            self.params.update_param(param_name='hmsdms', single_param=hmsdms_param, overwrite_existing=overwrite_existing)
        # other parameters from simbad
        if 'params' in simbad_doc:
            for param_name, param_dict in simbad_doc['params'].items():
                units = param_to_units[param_name]
                single_param = SingleParam.strict_format(param_name=param_name, units=units, **param_dict)
                self.params.update_param(param_name=param_name, single_param=single_param, overwrite_existing=overwrite_existing)
                if param_name == 'sptype':
                    sp_num_param = SingleParam.strict_format(param_name='sptype_num',
                        value=spectral_type_to_float(single_param.value), ref=single_param.ref, units='')
                    self.params.update_param(param_name='sptype_num', single_param=sp_num_param, overwrite_existing=overwrite_existing)

    def reduce(self):
        # absolute abundances
        for catalog_name in sorted(self.available_abundance_catalogs):
            single_catalog = self.__getattribute__(catalog_name)
            for element_name in single_catalog.available_abundances:
                abundance_record = single_catalog.__getattribute__(str(element_name))
                self.reduced_abundances['absolute'].add_abundance(abundance_record=abundance_record,
                                                                  element_name=element_name,
                                                                  catalog=catalog_name)
        # normalized abundances
        for catalog_name in sorted(self.available_abundance_catalogs):
            single_catalog = self.__getattribute__(catalog_name)
            for norm_key in sorted(single_catalog.normalizations):
                single_norm = single_catalog.__getattribute__(norm_key)
                for element_name in single_norm.available_abundances:
                    if norm_key not in self.reduced_abundances.keys():
                        # only make if there is data to put in it
                        self.reduced_abundances[norm_key] = ReducedAbundances()
                    abundance_record = single_norm.__getattribute__(str(element_name))
                    self.reduced_abundances[norm_key].add_abundance(abundance_record=abundance_record,
                                                                    element_name=element_name,
                                                                    catalog=catalog_name)
        for reduced_abundance in self.reduced_abundances.values():
            reduced_abundance.calc()

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
