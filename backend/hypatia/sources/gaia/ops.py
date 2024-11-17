from hypatia.sources.gaia.query import GaiaQuery
from hypatia.sources.simbad.ops import get_star_data
from hypatia.object_params import ObjectParams, SingleParam
from hypatia.sources.gaia.db import GaiaRef, parse_gaia_name


gaia_dr3_ref = 'Gaia DR3 Gaia Collaboration et al. (2016b) and Gaia Collaboration et al. (2022k)'
rename_params = {'ra_epochj2000': 'raj2000', 'dec_epochj2000': 'decj2000',
                 'pmra': 'pm_ra', 'pmdec': 'pm_dec'}
object_params_to_trim = {'ra', 'ra_error', 'dec', 'dec_error', 'ref_epoch', 'duplicated_source', 'source_id'}
special_case_params = {'r_est', 'r_lo', 'r_hi',
                       'teff_val', 'teff_percentile_upper', 'teff_percentile_lower',
                       'teff_gspphot', 'teff_gspphot_upper', 'teff_gspphot_lower',
                       'distance_gspphot', 'distance_gspphot_upper', 'distance_gspphot_lower',
                       'distance_msc', 'distance_msc_upper', 'distance_msc_lower',
                       }
param_to_units = {'raj2000': 'deg', 'decj2000': 'deg',
                  'ref_epoch': 'Julian Years', 'parallax': 'mas',
                  'pmra': 'mas/yr', 'pmdec': 'mas/yr',
                  'phot_g_mean_flux': 'e-/s', 'phot_g_mean_mag': 'mag',
                  'radial_velocity': 'km/s',
                  'teff_val': 'K', 'teff_percentile_lower': 'K', 'teff_percentile_upper': 'K',
                  'teff_gspphot': 'K', 'teff_gspphot_lower': 'K', 'teff_gspphot_upper': 'K',
                  'r_est': '[pc]', 'r_lo': '[pc]', 'r_hi': '[pc]', 'dist': '[pc]',
                  'distance_gspphot': '[pc]', 'distance_gspphot_lower': '[pc]', 'distance_gspphot_upper': '[pc]',}


def special_gaia_params(param_str: str, params_dicts, gaia_params_dict, param_names_found, gaia_ref, param_to_units):
    gaia_params_dict_keys = set(gaia_params_dict.keys())
    if 'dist' not in params_dicts.keys():
        params_dicts['dist'] = {}
    param_names_found.add('dist')
    main_value = gaia_params_dict[param_str]
    params_dicts['dist']['value'] = main_value
    params_dicts['dist']['ref'] = gaia_ref
    params_dicts['dist']['units'] = param_to_units[param_str]
    upper_key = f'{param_str}_upper'
    lower_key = f'{param_str}_lower'
    if upper_key in gaia_params_dict_keys:
        upper_error = gaia_params_dict[upper_key] - main_value
        del gaia_params_dict[upper_key]
    else:
        upper_error = None
    if lower_key in gaia_params_dict_keys:
        lower_error = gaia_params_dict[lower_key] - main_value
        del gaia_params_dict[lower_key]
    else:
        lower_error = None
    if lower_error is not None or upper_error is not None:
        params_dicts['dist']['err_low'] = lower_error
        params_dicts['dist']['err_high'] = upper_error
    del gaia_params_dict[param_str]
    return params_dicts


def convert_to_object_params(gaia_params_dicts):
    new_object_params = ObjectParams()
    for gaia_hypatia_name in gaia_params_dicts.keys():
        dr_number, _gaia_star_id = parse_gaia_name(gaia_hypatia_name)
        gaia_params_dict = gaia_params_dicts[gaia_hypatia_name]
        gaia_params_dict_keys = set(gaia_params_dict.keys())
        if dr_number == 3:
            ref_str = gaia_dr3_ref
        else:
            ref_str = f'Gaia Data Release {dr_number}'
        params_dicts = {}
        param_names_found = set()
        # handling for the distance from the Bailer-Jones Catalog
        if 'r_est' in gaia_params_dict_keys:
            params_dicts['dist'] = {}
            param_names_found.add('dist')
            params_dicts['dist']['value'] = gaia_params_dict['r_est']
            params_dicts['dist']['ref'] = 'Bailer-Jones et al. (2018)'
            params_dicts['dist']['units'] = param_to_units['r_est']
            if 'r_hi' in gaia_params_dict_keys:
                upper_error = gaia_params_dict['r_hi'] - gaia_params_dict['r_est']
            else:
                upper_error = None
            if 'r_lo' in gaia_params_dict_keys:
                lower_error = gaia_params_dict['r_lo'] - gaia_params_dict['r_est']
            else:
                lower_error = None
            if lower_error is not None or upper_error is not None:
                params_dicts['dist']['err_low'] = lower_error
                params_dicts['dist']['err_high'] = upper_error
        if 'distance_gspphot' in gaia_params_dict_keys:
            special_gaia_params('distance_gspphot', params_dicts, gaia_params_dict, param_names_found,
                                gaia_dr3_ref, param_to_units)
        if 'distance_msc' in gaia_params_dict_keys:
            special_gaia_params('distance_msc', params_dicts, gaia_params_dict, param_names_found,
                                gaia_dr3_ref, param_to_units)
        if 'teff_val' in gaia_params_dict_keys:
            params_dicts['teff'] = {}
            param_names_found.add('teff')
            params_dicts['teff']['value'] = gaia_params_dict['teff_val']
            params_dicts['teff']['ref'] = ref_str
            params_dicts['teff']['units'] = param_to_units['teff_val']
            if 'teff_percentile_upper' in gaia_params_dict_keys:
                upper_error = gaia_params_dict['teff_percentile_upper'] - gaia_params_dict['teff_val']
            else:
                upper_error = None
            if 'teff_percentile_lower' in gaia_params_dict_keys:
                lower_error = gaia_params_dict['teff_percentile_lower'] - gaia_params_dict['teff_val']
            else:
                lower_error = None
            if lower_error is not None or upper_error is not None:
                params_dicts['teff']['err'] = (lower_error, upper_error)
        elif 'teff_gspphot' in gaia_params_dict_keys:
            params_dicts['teff'] = {}
            param_names_found.add('teff')
            params_dicts['teff']['value'] = gaia_params_dict['teff_gspphot']
            params_dicts['teff']['ref'] = ref_str
            params_dicts['teff']['units'] = param_to_units['teff_gspphot']
            if 'teff_gspphot_upper' in gaia_params_dict_keys:
                upper_error = gaia_params_dict['teff_gspphot_upper'] - gaia_params_dict['teff_gspphot']
                del gaia_params_dict['teff_gspphot_upper']
            else:
                upper_error = None
            if 'teff_gspphot_lower' in gaia_params_dict_keys:
                lower_error = gaia_params_dict['teff_gspphot_lower'] - gaia_params_dict['teff_gspphot']
                del gaia_params_dict['teff_gspphot_lower']
            else:
                lower_error = None
            if lower_error is not None or upper_error is not None:
                params_dicts['teff']['err_low'] = lower_error
                params_dicts['teff']['err_high'] = upper_error
            del gaia_params_dict['teff_gspphot']
        for param_key in gaia_params_dict_keys - special_case_params:
            if '_error' in param_key:
                param_name = param_key.replace('_error', '')
                if param_name not in param_names_found:
                    params_dicts[param_name] = {}
                    param_names_found.add(param_name)
                params_dicts[param_name]['err_low'] = params_dicts[param_name]['err_high'] \
                    = gaia_params_dict[param_key]
            else:
                if param_key not in param_names_found:
                    params_dicts[param_key] = {}
                    param_names_found.add(param_key)
                params_dicts[param_key]['value'] = gaia_params_dict[param_key]
                params_dicts[param_key]['ref'] = ref_str
                if param_key in param_to_units.keys():
                    params_dicts[param_key]['units'] = param_to_units[param_key]
        param_names = set(params_dicts.keys()) - object_params_to_trim
        for param_name in param_names:
            dict_this_param = params_dicts[param_name]
            if 'err' in dict_this_param.keys():
                dict_this_param['err_low'], dict_this_param['err_high'] = dict_this_param['err']
                del dict_this_param['err']
            param_name_lower = param_name.lower()
            if param_name_lower in rename_params.keys():
                final_param_name = rename_params[param_name_lower]
            else:
                final_param_name = param_name_lower
            new_object_params[final_param_name] = SingleParam.strict_format(param_name=final_param_name,
                                                                            **dict_this_param)
    return new_object_params

class GaiaLib:
    max_dr_number = 3
    dr_numbers = list(range(1, max_dr_number + 1))
    gaia_name_types = {f'gaia dr{dr_number}' for dr_number in dr_numbers}

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.gaiadr1_ref = GaiaRef(verbose=self.verbose, dr_number=1)
        self.gaiadr2_ref = GaiaRef(verbose=self.verbose, dr_number=2)
        self.gaiadr3_ref = GaiaRef(verbose=self.verbose, dr_number=3)
        self.gaia_query = GaiaQuery(verbose=self.verbose)

    def batch_update(self, dr_number, simbad_formatted_names_list):
        dr_number = int(dr_number)
        gaia_ref = self.__getattribute__(f'gaiadr{dr_number}_ref')
        self.gaia_query.astroquery_source(simbad_formatted_name_list=simbad_formatted_names_list, dr_num=dr_number)
        gaia_ref.save_many_records(self.gaia_query.star_dict.values())

    def get_gaia_names_dict(self, star_name: str) -> tuple[str, dict[str, str]]:
        star_data_doc = get_star_data(star_name)
        attr_name = star_data_doc['attr_name']
        available_gaia_name_types = set(star_data_doc.keys()) & self.gaia_name_types
        gaia_star_names_dict = {star_type: star_data_doc[star_type] for star_type in available_gaia_name_types}
        return attr_name, gaia_star_names_dict

    def get_single_dr_number_data(self, gaia_name):
        dr_number, gaia_star_id = parse_gaia_name(gaia_name)
        gaia_ref = self.__getattribute__(f'gaiadr{dr_number}_ref')
        test_output = gaia_ref.find(gaia_star_id=gaia_star_id)
        if test_output is None:
            # is data available on the ESA website?
            self.gaia_query.astroquery_source([gaia_name], dr_num=dr_number)
            if gaia_star_id in self.gaia_query.star_dict.keys():
                # We found the data and can update the reference data so that it is found first next time
                gaia_params_dict = self.gaia_query.star_dict[gaia_star_id]
            else:
                # no data was found, we record this so that next time a search is not needed.
                gaia_params_dict = {}
            gaia_ref.save_record(gaia_params_dict)
            # we try again to get the data, this time it should be found.
            return self.get_single_dr_number_data(gaia_name)
        # This is the default case, data is available in the reference collection, and is returned
        return test_output

    def get_params_data(self, star_name: str) -> tuple[str, dict[str, any]]:
        attr_name, gaia_star_names_dict = self.get_gaia_names_dict(star_name=star_name)
        return attr_name, {gaia_name: self.get_single_dr_number_data(gaia_name)
                           for gaia_name in gaia_star_names_dict.values()}

    def get_object_params(self, star_name: str):
        attr_name, gaia_params_dicts = self.get_params_data(star_name=star_name)
        return attr_name, convert_to_object_params(gaia_params_dicts=gaia_params_dicts)


if __name__ == '__main__':
    gl = GaiaLib(verbose=True)
    hypatia_attr_name, gaia_params = gl.get_params_data(star_name='HD 1234')
