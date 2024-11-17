import time
import importlib

import numpy as np
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord, Distance

from hypatia.sources.gaia.db import astro_query_dr1_params, astro_query_dr2_params, astro_query_dr3_params


deg_per_mas = 1.0 / (1000.0 * 60.0 * 60.0)


def simple_job_text(dr_num, sub_list):
    fields = '*'
    if dr_num == 3:
        fields = ', '.join([name.upper() for name in sorted(astro_query_dr3_params)])
    job_text = f'SELECT {fields} FROM gaiadr{dr_num}.gaia_source WHERE source_id={sub_list[0]}'
    if len(sub_list) > 1:
        for list_index in range(1, len(sub_list)):
            job_text += ' OR source_id=' + str(sub_list[list_index])
    return job_text


class GaiaQuery:
    batch_size = 500

    def __init__(self, verbose=False):
        # import this package at 'runtime' not 'import time' to avoid an unnecessary connection to the Gaia SQL server
        self.astro_query_gaia = importlib.import_module('astroquery.gaia')
        self.Gaia = self.astro_query_gaia.Gaia
        self.verbose = verbose
        self.gaia_dr1_data = None
        self.gaia_dr2_data = None
        self.gaia_dr3_data = None
        self.star_dict = None

        self.astro_query_dr1_params = set(astro_query_dr1_params)
        self.astro_query_dr2_params = set(astro_query_dr2_params)
        self.astro_query_dr3_params = set(astro_query_dr3_params)

    def astroquery_get_job(self, job, dr_num=2):
        while job._phase != 'COMPLETED':
            time.sleep(1)
        raw_results = job.get_results()
        sources_dict = {}

        if dr_num == 1:
            query_params = self.astro_query_dr1_params
        elif dr_num == 2:
            query_params = self.astro_query_dr2_params
        elif dr_num == 3:
            query_params = self.astro_query_dr3_params
        else:
            raise KeyError(f'The given Gaia Data Release number {str(dr_num)} is not of the format.')

        column_names = set(raw_results.columns)
        lower_to_column_names = {column_name.lower(): column_name for column_name in column_names}
        for index in range(len(raw_results.columns[lower_to_column_names['source_id']])):
            params_dict = {param: raw_results.columns[lower_to_column_names[param]][index] for param in set(lower_to_column_names.keys()) & query_params
                           if not np.ma.is_masked(raw_results.columns[lower_to_column_names[param]][index])}
            found_params = set(params_dict.keys())
            if {'ra', 'dec', 'pmra', 'pmdec', 'ref_epoch'} - found_params == set():
                # if parallax is available, do a more precise calculation using the distance.
                if np.ma.is_masked(params_dict['parallax']) or params_dict['parallax'] < 0.0:
                    icrs = SkyCoord(ra=params_dict['ra'] * u.deg, dec=params_dict['dec'] * u.deg,
                                    pm_ra_cosdec=params_dict['pmra'] * u.mas / u.yr,
                                    pm_dec=params_dict['pmdec'] * u.mas / u.yr,
                                    obstime=Time(params_dict['ref_epoch'], format='decimalyear'))
                else:
                    icrs = SkyCoord(ra=params_dict['ra'] * u.deg, dec=params_dict['dec'] * u.deg,
                                    distance=Distance(parallax=params_dict['parallax'] * u.mas, allow_negative=False),
                                    pm_ra_cosdec=params_dict['pmra'] * u.mas / u.yr,
                                    pm_dec=params_dict['pmdec'] * u.mas / u.yr,
                                    obstime=Time(params_dict['ref_epoch'], format='decimalyear'))
                J2000 = icrs.apply_space_motion(Time(2000.0, format='decimalyear'))
                params_dict['raj2000'] = J2000.ra.degree
                params_dict['decj2000'] = J2000.dec.degree
                params_dict['raj2000_error'] = params_dict['ra_error'] * deg_per_mas
                params_dict['decj2000_error'] = params_dict['dec_error'] * deg_per_mas
            sources_dict[params_dict['source_id']] = {param.lower(): params_dict[param] for param in params_dict.keys()
                                                      if params_dict[param] != '--'}
        return sources_dict

    def astroquery_source(self, simbad_formatted_name_list, dr_num=2):
        list_of_sub_lists = []
        sub_list = []
        cut_index = len('Gaia DR# ')
        cut_name_list = [gaia_name[cut_index:] for gaia_name in simbad_formatted_name_list]
        for source_id in cut_name_list:
            if len(sub_list) == self.batch_size:
                list_of_sub_lists.append(sub_list)
                sub_list = [source_id]
            else:
                sub_list.append(source_id)
        list_of_sub_lists.append(sub_list)
        self.star_dict = {}
        for sub_list in list_of_sub_lists:
            if dr_num == 2:
                job_text = f'SELECT * FROM gaiadr{dr_num}.gaia_source AS g, ' + \
                           'external.gaiadr2_geometric_distance AS d ' + \
                           f'WHERE (g.source_id={str(sub_list[0])} AND d.source_id = g.source_id)'
                if len(sub_list) > 1:
                    for list_index in range(1, len(sub_list)):
                        job_text += f' OR (g.source_id={str(sub_list[list_index])} AND d.source_id = g.source_id)'
            else:
                job_text = simple_job_text(dr_num, sub_list)
            job = self.Gaia.launch_job_async(job_text)
            sources_dict = self.astroquery_get_job(job, dr_num=dr_num)
            redo_ids = [source_id for source_id in
                        {int(source_id_str) for source_id_str in sub_list} - set(sources_dict.keys())]
            if redo_ids:
                job_text = simple_job_text(dr_num, redo_ids)
                job = self.Gaia.launch_job_async(job_text)
                sources_dict.update(self.astroquery_get_job(job, dr_num=dr_num))
            self.star_dict.update({gaia_id_int: sources_dict[gaia_id_int] for gaia_id_int in sources_dict.keys()})
