import os
import pickle

from hypatia.query.gaia import GaiaLib
from hypatia.load.solar import SolarNorm
from hypatia.load.table_read import row_dict
from hypatia.load.catalogs import get_catalogs
from hypatia.load.star_params import Pastel, Xhip
from hypatia.analyze.all_star_data import AllStarData
from hypatia.analyze.output_star_data import OutputStarData
from hypatia.data_structures.object_params import SingleParam
from hypatia.database.name_db import get_main_id, get_star_data
from hypatia.database.tic_db import get_tic_data, tic_reference, units_dict
from hypatia.config import working_dir, ref_dir, abundance_dir, hacked, pickle_nat


def load_catalog_query():
    return pickle.load(open(pickle_nat, 'rb'))


class NatCat:
    requested_pastel_params = {"logg", "logg_std", "teff", "teff_std", "bmag", "bmag_std", "vmag", "vmag_std", "author"}
    xhip_params = {"RAJ2000", "DECJ2000", "Plx", "e_Plx", "pmRA", "pmDE", "GLon", "Glat", "Dist", "X",
                   "Y", "Z", "SpType", "RV", "U", "V", "W", "Bmag", "Vmag", "TWOMASS", "Lum", "rSpType",
                   "BV"}

    def __init__(self, params_list_for_stats=None, star_types_for_stats=None,
                 catalogs_from_scratch=False, verbose=False, catalogs_verbose=True,
                 get_abundance_data=True, get_exo_data=False, refresh_exo_data=False,
                 target_list=None,  fast_update_gaia=False,
                 catalogs_file_name=None, abundance_data_path=None):
        self.verbose = verbose
        self.catalogs_verbose = catalogs_verbose

        self.catalogs_from_scratch = catalogs_from_scratch

        self.refresh_exo_data = refresh_exo_data
        self.catalogs_file_name = catalogs_file_name
        self.abundance_data_path = abundance_data_path

        # populated some default values
        if params_list_for_stats is None:
            params_list_for_stats = ["dist", "teff", "vmag", "SpType"]
        if star_types_for_stats is None:
            star_types_for_stats = ['gaia dr2', "gaia dr1", "hip", "hd"]

        # reference data
        self.normalization_ref = row_dict(os.path.join(ref_dir, "solar_norm_ref.csv"), key='catalog')
        self.xhip = Xhip()
        self.pastel = Pastel()

        # initialization and preferences
        self.params_list_for_stats = [param.lower() for param in params_list_for_stats]
        self.star_types_for_stats = star_types_for_stats

        self.text_file_dir = os.path.join(working_dir, "load", 'data_products')

        # variable that are populated in methods within this class
        self.catalog_dict = None
        self.output_norm = None

        self.star_data = AllStarData(verbose=self.verbose)
        self.init_catalogs = set()
        self.unreferenced_stars = None

        self.xo = None

        # get the solar normalization data
        sn = SolarNorm()
        self.solar_norm_dict = sn()
        self.norm_keys = set(self.solar_norm_dict.keys())

        self.star_data = AllStarData()
        if get_abundance_data:
            self.catalog_data()
        if get_exo_data:
            self.xo_data()
        self.targets_requested = self.targets_found = self.targets_not_found = None
        if target_list is not None:
            self.target_data(target_list)
        if fast_update_gaia:
            self.star_data.fast_update_gaia()
        self.get_params()
        self.stats_for_star_data()
        self.stats = self.star_data.stats
        self.star_data.find_available_attributes()

    def catalog_data(self):
        if self.verbose:
            print('\nLoading and mapping the stellar abundance data...')
            print("  Loading Abundance catalog data...")
        self.catalog_dict = get_catalogs(from_scratch=self.catalogs_from_scratch,
                                         local_abundance_dir=self.abundance_data_path,
                                         catalogs_file_name=self.catalogs_file_name,
                                         verbose=self.catalogs_verbose)
        if self.catalogs_from_scratch:
            if self.verbose:
                print("    Saving Abundance data to pickle files...")
            for catalog_short_name in self.catalog_dict.keys():
                self.catalog_dict[catalog_short_name].save()
            if self.verbose:
                print("      Saving complete.")
        if self.verbose:
            print('    Abundance data load and processed.')
            print("  Linking abundance data to stellar objects...")
        self.init_catalogs = set(self.catalog_dict.keys())
        self.star_data.get_abundances(all_catalogs=self.catalog_dict)
        if self.verbose:
            print("Stellar abundance data acquired.\n")

    def xo_data(self):
        self.xo = self.star_data.get_exoplanets(refresh_exo_data=self.refresh_exo_data)

    def target_data(self, target_list: list[str] or str):
        if self.verbose:
            print('Getting data for targets...')
        if isinstance(target_list, str):
            with open(target_list, 'r') as f:
                target_list = [name.strip() for name in f.readlines()]
        star_name_ids = [get_main_id(target_name) for target_name in target_list]
        if self.verbose:
            print('  Hypatia handles acquired for target stars.')
        self.star_data.get_targets(main_star_ids=star_name_ids)
        self.targets_found = self.star_data.targets_found
        self.targets_not_found = self.star_data.targets_not_found
        if self.verbose:
            print(F'Target Data Acquired.')
            print(F'  Targets requested: {"%3i" % len(target_list)} : {sorted(star_name_ids)}')
            print(F'      Targets found: {"%3i" % len(self.targets_found)} : {sorted(self.targets_found)}')
            print(F'  Targets not found: {"%3i" % len(self.targets_not_found)} : {sorted(self.targets_not_found)}\n')

    def get_params(self, get_gaia_params=True, get_pastel_params=True, get_tic_params=True, get_hipparcos_params=True):
        if self.verbose:
            print("Acquiring stellar parameter data...")
        if get_gaia_params:
            """
            The gaia data that is first in the list variable "gaia_data_list", will have the highest priory for
            populating the values for Gaia parameters. For example if you prefer to have the latest released value
            for the parameter distance (dist), make sure that the latest Gia release is first in this list.
            """
            gaia_lib = GaiaLib(verbose=self.verbose)
            for reference_star_name in self.star_data.star_names:
                single_star = self.star_data.__getattribute__(reference_star_name)
                star_names_dict = single_star.star_names_dict
                hypatia_handle, gaia_params_dict = gaia_lib.get_object_params(star_names_dict)
                if hypatia_handle != reference_star_name:
                    raise KeyError("The Gaia parameters returned a different hypatia handle then the star they were " +
                                   "associated with.")
                single_star.gaia_params(gaia_params_dict)
            if self.verbose:
                print("  Gaia stellar parameters acquired.")

        # Star Parameters from the Pastel Catalog (effective temperature and Log values for surface gravity)
        if get_pastel_params:

            if self.pastel.pastel_ave is None:
                self.pastel.load()
            pastel_name_types = set(self.pastel.pastel_ave.keys())
            for reference_star_name in self.star_data.star_names:
                self.star_data.__getattribute__(reference_star_name).pastel_params(pastel_name_types,
                                                                                   self.pastel,
                                                                                   self.requested_pastel_params)
            if self.verbose:
                print("  Pastel stellar parameters acquired.")

        # Stellar Parameters from the Tess Input Catalog
        if get_tic_params:
            tic_params_rename = {"mass": "st_mass", "rad": "st_rad"}
            rename_keys = set(tic_params_rename.keys())
            self.tic.make_ref_data_look_up_dicts()
            tic_batch_update = False
            update_trigger = True
            for hypatia_handle in sorted(self.star_data.star_names):
                star_names_dict = self.star_data.__getattribute__(hypatia_handle).star_names_dict
                if self.tic.new_data_count < self.tic_batch_update_rate + 1:
                    requested_tic_dict = self.tic.get_object_params(star_names_dict, update_ref=True)
                else:
                    requested_tic_dict = self.tic.get_object_params(star_names_dict, update_ref=False)
                    tic_batch_update = True
                    if self.tic.new_data_count % self.tic_batch_update_rate == 0:
                        if update_trigger:
                            self.tic.update_ref()
                            update_trigger = False
                    else:
                        update_trigger = True
                if requested_tic_dict:
                    self.star_data.__getattribute__(hypatia_handle).params.update_params(requested_tic_dict,
                                                                                         overwrite_existing=False)
            if tic_batch_update and self.tic.new_tic_data:
                self.tic.update_ref()
            if self.verbose:
                print("  Tess Input Catalog stellar parameters acquired.")

        # Parameters for the Hipparcos Survey
        if get_hipparcos_params:
            if self.xhip.ref_data is None:
                self.xhip.load()
            rename_dict = {"X": "X_pos", "Y": "Y_pos", "Z": "Z_pos", "U": "U_vel", "V": "V_vel", "W": "W_vel"}
            available_xhip_ids = set(self.xhip.ref_data.keys())
            for reference_star_name in self.star_data.star_names:
                single_star = self.star_data.__getattribute__(reference_star_name)
                single_star.xhip_params(self.xhip, available_xhip_ids, self.xhip_params, rename_dict)
            if self.verbose:
                print("  X-Hipparcos stellar parameters acquired.")

        # calculated parameters
        for reference_star_name in self.star_data.star_names:
            self.star_data.__getattribute__(reference_star_name).params.calculated_params()
        if self.verbose:
            print("Stellar parameters acquired, reference is up-to-data, and calculations completed\n")

        # hacked parameters to add at the last minute (from config.py)
        for string_name in hacked.keys():
            param, value = hacked[string_name]
            hacked_single_param = SingleParam(value=value, ref='from config.py, the "hacked" variable')
            simbad_doc = get_star_data(test_name=string_name, test_origin="hacked")
            main_star_id = simbad_doc["_id"]
            if main_star_id in self.star_data.star_names:
                this_star = self.star_data.__getattribute__(simbad_doc['attr_name'])
                this_star.params.update_param(param, hacked_single_param, overwrite_existing=False)

    def get_unreferenced_stars(self):
        self.unreferenced_stars = {key: self.catalog_dict[key].unreferenced_stars for key in self.catalog_dict.keys()
                                   if self.catalog_dict[key].unreferenced_stars != []}
        return self.unreferenced_stars

    def stats_for_star_data(self, star_data=None):
        if star_data is None:
            star_data = self.star_data
        star_data.do_stats(solar_norm_dict=self.solar_norm_dict, params_set=self.params_list_for_stats,
                           star_name_types=self.star_types_for_stats)

    def make_output_star_data(self, star_data=None,
                              target_catalogs=None, or_logic_for_catalogs=True,
                              catalogs_return_only_targets=False,
                              target_star_name_types=None, and_logic_for_star_names=True,
                              target_params=None, and_logic_for_params=True,
                              target_elements=None, or_logic_for_element=True,
                              min_catalog_count=None,
                              parameter_bound_filter=None,
                              parameter_match_filter=None,
                              has_exoplanet=None,
                              at_least_fe_and_another=False,
                              remove_nlte_abundances=False,
                              keep_complement=False,
                              is_target=None,
                              norm_key=None,
                              write_out=False, output_dir=None, exo_mode=False,
                              star_data_stats=True,
                              reduce_abundances=True):
        """
        :param norm_key: All solar normalizations can be called via the names in "solar_norm_ref" file. Note
        that the normalization that is the original Grevesse98 is now called grev98-th_thii_del_peloso05b, since it
        was appended to with Th and ThII from del Peloso05b. The other two ways to normalize the data are either by
        leaving the data as absolute, in which case norm_key=None, or using the original normalization, which is
        specially handled in output_star_data (norm_key="original).
        """
        if star_data is None:
            star_data = self.star_data
        output_star_data = OutputStarData()
        output_star_data.receive_data(star_data)
        output_star_data.filter(target_catalogs=target_catalogs, or_logic_for_catalogs=or_logic_for_catalogs,
                                catalogs_return_only_targets=catalogs_return_only_targets,
                                target_star_name_types=target_star_name_types,
                                and_logic_for_star_names=and_logic_for_star_names,
                                target_params=target_params, and_logic_for_params=and_logic_for_params,
                                target_elements=target_elements, or_logic_for_element=or_logic_for_element,
                                min_catalog_count=min_catalog_count,
                                parameter_bound_filter=parameter_bound_filter,
                                parameter_match_filter=parameter_match_filter,
                                has_exoplanet=has_exoplanet,
                                at_least_fe_and_another=at_least_fe_and_another,
                                remove_nlte_abundances=remove_nlte_abundances,
                                keep_complement=keep_complement,
                                is_target=is_target)
        if norm_key is not None:
            output_star_data.normalize(norm_key=norm_key)
        if write_out:
            output_star_data.output_file(output_dir=output_dir, exo_mode=exo_mode)
        if star_data_stats:
            output_star_data.do_stats(solar_norm_dict=self.solar_norm_dict, params_set=self.params_list_for_stats,
                                      star_name_types=self.star_types_for_stats)
        if reduce_abundances:
            output_star_data.reduce_elements()
        output_star_data.find_available_attributes()
        return output_star_data

    def pickle_myself(self):
        if self.verbose:
            print("Picking an entire NatCat class.\nFile name:", pickle_nat)
        pickle.dump(self, open(pickle_nat, 'wb'))
        if self.verbose:
            print("  pickling complete.")

    def output_abs_abundances(self):
        output_dir = os.path.join(abundance_dir, 'absolute')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        for catalog_name in self.catalog_dict.keys():
            single_catalog = self.catalog_dict[catalog_name]
            single_catalog.write_catalog(target="un_norm", update_catalog_list=False,
                                         add_to_git=False, output_dir=output_dir)

    def output_raw_abundances(self):
        output_dir = os.path.join(abundance_dir, 'raw')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        for catalog_name in self.catalog_dict.keys():
            single_catalog = self.catalog_dict[catalog_name]
            single_catalog.write_catalog(target="raw", update_catalog_list=False,
                                         add_to_git=False, output_dir=output_dir)
