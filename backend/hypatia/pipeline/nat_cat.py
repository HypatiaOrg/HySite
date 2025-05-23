import os
import pickle

from hypatia.sources.xhips import Xhip
from hypatia.sources.gaia.ops import GaiaLib
from hypatia.object_params import SingleParam
from hypatia.tools.table_read import row_dict
from hypatia.pipeline.star.all import AllStarData
from hypatia.configs.source_settings import hacked
from hypatia.sources.tic.ops import get_hy_tic_data
from hypatia.tools.color_text import file_name_text
from hypatia.sources.pastel.ops import get_pastel_data
from hypatia.pipeline.star.output import OutputStarData
from hypatia.sources.catalogs.solar_norm import SolarNorm
from hypatia.sources.catalogs.catalogs import get_catalogs
from hypatia.sources.simbad.batch import get_star_data_batch
from hypatia.sources.simbad.ops import get_main_id, get_star_data
from hypatia.configs.file_paths import working_dir, ref_dir, abundance_dir, pickle_nat, default_catalog_file


def load_catalog_query():
    return pickle.load(open(pickle_nat, 'rb'))


class NatCat:

    def __init__(self, params_list_for_stats=None, star_types_for_stats=None,
                 catalogs_from_scratch=True, verbose=False, catalogs_verbose=True,
                 get_abundance_data=True, get_exo_data=False, refresh_exo_data=False,
                 target_list: list[str] | list[tuple[str, ...]] | str | os.PathLike | None = None,  fast_update_gaia=False,
                 catalogs_file_name=None, abundance_data_path=None):
        self.verbose = verbose
        self.catalogs_verbose = catalogs_verbose

        self.catalogs_from_scratch = catalogs_from_scratch

        self.refresh_exo_data = refresh_exo_data
        if catalogs_file_name is None:
            self.catalogs_file_name = default_catalog_file
        else:
            self.catalogs_file_name = catalogs_file_name
        self.abundance_data_path = abundance_data_path

        # populated some default values
        if params_list_for_stats is None:
            params_list_for_stats = ['dist', 'teff', 'vmag', 'SpType']
        if star_types_for_stats is None:
            star_types_for_stats = ['gaia dr2', 'gaia dr1', 'hip', 'hd']

        # reference data
        self.normalization_ref = row_dict(os.path.join(ref_dir, 'solar_norm_ref.csv'), key='catalog')
        self.xhip = Xhip()

        # initialization and preferences
        self.params_list_for_stats = [param.lower() for param in params_list_for_stats]
        self.star_types_for_stats = star_types_for_stats

        self.text_file_dir = os.path.join(working_dir, 'load', 'data_products')

        # variables that are populated in methods
        self.catalog_dict = None
        self.output_norm = None

        self.star_data = AllStarData(verbose=self.verbose)
        self.init_catalogs = set()
        self.unreferenced_stars = None

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
            print('  Loading Abundance catalog data...')
        self.catalog_dict = get_catalogs(from_scratch=self.catalogs_from_scratch,
                                         local_abundance_dir=self.abundance_data_path,
                                         catalogs_file_name=self.catalogs_file_name,
                                         verbose=self.catalogs_verbose)
        if self.catalogs_from_scratch:
            if self.verbose:
                print('    Saving Abundance data to pickle files...')
            for catalog_short_name in self.catalog_dict.keys():
                self.catalog_dict[catalog_short_name].save()
            if self.verbose:
                print('      Saving complete.')
        if self.verbose:
            print('    Abundance data load and processed.')
            print('  Linking abundance data to stellar objects...')
        self.init_catalogs = set(self.catalog_dict.keys())
        self.star_data.get_abundances(all_catalogs=self.catalog_dict)
        if self.verbose:
            print('Stellar abundance data acquired.\n')

    def xo_data(self):
        self.star_data.get_exoplanets(refresh_exo_data=self.refresh_exo_data)

    def target_data(self, target_list: list[str] | list[tuple[str, ...]] | str | os.PathLike):
        if self.verbose:
            print('Getting data for targets...')
        if isinstance(target_list, str) or isinstance(target_list, os.PathLike):
            if str(target_list).endswith('.psv'):
                delimiter = '|'
            else:
                delimiter = ','
            with open(target_list, 'r') as f:
                target_list = [tuple(star_name.strip() for star_name in row_of_star_names.split(delimiter))
                               for row_of_star_names in f.readlines()]
        search_ids = [tuple(row_of_star_names,) if isinstance(row_of_star_names, str) else row_of_star_names
                      for row_of_star_names in target_list]
        star_docs = get_star_data_batch(search_ids=search_ids, test_origin='target_data')
        star_ids = [get_main_id(star_doc['_id']) for star_doc in star_docs]
        if self.verbose:
            print('  Hypatia handles acquired for target stars.')
        self.star_data.get_targets(target_star_ids=star_ids)
        self.targets_found = self.star_data.targets_found
        self.targets_not_found = self.star_data.targets_not_found
        if self.verbose:
            print(F'Target Data Acquired.')
            print(F'  Targets requested: {'%3i' % len(search_ids)} : {sorted(star_ids)}')
            print(F'      Targets found: {'%3i' % len(self.targets_found)} : {sorted(self.targets_found)}')
            print(F'  Targets not found: {'%3i' % len(self.targets_not_found)} : {sorted(self.targets_not_found)}\n')

    def get_params(self, get_gaia_params: bool = True, get_pastel_params: bool = True, get_exo_params: bool = True,
                   get_tic_params: bool = True, get_hipparcos_params: bool = True, get_simbad_params: bool = True):
        if self.verbose:
            print('Acquiring stellar parameter data...')
        gaia_lib = None
        pastel_data = None
        print_int = round(len(self.star_data) / 20)
        for star_index, single_star in list(enumerate(self.star_data)):
            if self.verbose and star_index % print_int == 0:
                print(f'  {star_index:6} of {len(self.star_data)} stars processed.')
            main_star_id = single_star.star_reference_name
            # Star Parameters from the Pastel Data Set
            if get_pastel_params:
                # Star Parameters from the Pastel Catalog (effective temperature and Log values for surface gravity)
                if pastel_data is None:
                    pastel_data = get_pastel_data(verbose=self.verbose)
                if main_star_id in pastel_data.keys():
                    pastel_record = pastel_data[main_star_id]
                    single_star.pastel_params(pastel_record)
            # Star Parameters from the Gaia Catalog
            if get_gaia_params:
                if gaia_lib is None:
                    gaia_lib = GaiaLib(verbose=self.verbose)
                _attr_name, gaia_params_dict = gaia_lib.get_object_params(main_star_id)
                single_star.gaia_params(gaia_params_dict)
            # Stellar Parameters from the Exoplanet Catalog
            if get_exo_params:
                single_star.exo_params()
            # Stellar Parameters from the Tess Input Catalog
            if get_tic_params:
                requested_tic = get_hy_tic_data(single_star.star_reference_name)
                if requested_tic is not None:
                    single_star.params.update_params(requested_tic, overwrite_existing=False)
            # add SIMBAD params
            if get_simbad_params:
                single_star.simbad_params(overwrite_existing=False)
            # Parameters for the Hipparcos Survey
            if get_hipparcos_params:
                if self.xhip.ref_data is None:
                    self.xhip.load(verbose=self.verbose)
                if 'hip' in single_star.simbad_doc.keys():
                    hip_name = single_star.simbad_doc['hip']
                    xhip_params_dict = self.xhip.get_xhip_data(hip_name=hip_name)
                    if xhip_params_dict is not None:
                        single_star.xhip_params(xhip_params_dict)
            # calculated parameters based on the available parameters
            single_star.params.calculated_params()

        # hacked parameters to add at the last minute (from config.py)
        for string_name in hacked.keys():
            param, value, units, ref = hacked[string_name]
            hacked_single_param = SingleParam(value=value, units=units, ref=ref)
            simbad_doc = get_star_data(test_name=string_name, test_origin='hacked')
            main_star_id = simbad_doc['_id']
            if main_star_id in self.star_data.star_names:
                this_star = self.star_data.__getattribute__(simbad_doc['attr_name'])
                this_star.params.update_param(param, hacked_single_param, overwrite_existing=False)
        if self.verbose:
            print('Stellar parameters acquired, reference is up-to-data, and calculations completed\n')

    def get_unreferenced_stars(self):
        self.unreferenced_stars = {key: self.catalog_dict[key].unreferenced_stars for key in self.catalog_dict.keys()
                                   if self.catalog_dict[key].unreferenced_stars != []}
        return self.unreferenced_stars

    def stats_for_star_data(self, star_data=None):
        if star_data is None:
            star_data = self.star_data
        star_data.do_stats(params_set=self.params_list_for_stats,
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
                              norm_keys: list[str] = None,
                              star_data_stats=True,
                              reduce_abundances=True):
        """
        :param norm_keys: list[s]: All solar normalizations can be called via the names in "solar_norm_ref" file. Note
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
        if norm_keys is not None:
            output_star_data.normalize(norm_keys=norm_keys)
        if star_data_stats:
            output_star_data.do_stats(params_set=self.params_list_for_stats,
                                      star_name_types=self.star_types_for_stats)
        if reduce_abundances:
            output_star_data.reduce_elements()
        output_star_data.find_available_attributes()
        return output_star_data

    def pickle_myself(self):
        if self.verbose:
            print('Picking an entire NatCat class.\nFile name:', file_name_text(pickle_nat))
        pickle.dump(self, open(pickle_nat, 'wb'))
        if self.verbose:
            print('  pickling complete.')

    def output_abs_abundances(self):
        output_dir = os.path.join(abundance_dir, 'absolute')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        for catalog_name in self.catalog_dict.keys():
            single_catalog = self.catalog_dict[catalog_name]
            single_catalog.write_catalog(target='un_norm', update_catalog_list=False,
                                         add_to_git=False, output_dir=output_dir)

    def output_raw_abundances(self):
        output_dir = os.path.join(abundance_dir, 'raw')
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        for catalog_name in self.catalog_dict.keys():
            single_catalog = self.catalog_dict[catalog_name]
            single_catalog.write_catalog(target='raw', update_catalog_list=False,
                                         add_to_git=False, output_dir=output_dir)
