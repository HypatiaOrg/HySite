import time
import json
from datetime import datetime
import http.client as httplib
import urllib.parse as urllib
from xml.dom.minidom import parseString

import numpy as np
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import SkyCoord, Distance

from hypatia.sources.gaia.db import astro_query_dr1_params, astro_query_dr2_params, astro_query_dr3_params


deg_per_mas = 1.0 / (1000.0 * 60.0 * 60.0)


class GaiaQuery:
    batch_size = 500
    cut_index = len('Gaia DR# ')
    astro_query_dr1_params = set(astro_query_dr1_params)
    astro_query_dr2_params = set(astro_query_dr2_params)
    astro_query_dr3_params = set(astro_query_dr3_params)
    host = "gea.esac.esa.int"
    port = 443
    pathinfo = "/tap-server/tap/async"

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.gaia_dr1_data = None
        self.gaia_dr2_data = None
        self.gaia_dr3_data = None
        self.star_dict = None

    def get_query_params(self, dr_num: int) -> set[str]:
        if dr_num == 1:
            requested_params = self.astro_query_dr1_params
        elif dr_num == 2:
            requested_params = self.astro_query_dr2_params
        elif dr_num == 3:
            requested_params = self.astro_query_dr3_params
        else:
            raise ValueError(f"The given Gaia Data Release number {str(dr_num)} is not expected.")
        return requested_params

    def wait_for_job(self, jobid):
        # Check job status, wait until finished
        while True:
            connection = httplib.HTTPSConnection(self.host, self.port)
            connection.request("GET", self.pathinfo + "/" + jobid)
            response = connection.getresponse()
            data = response.read()

            # XML response: parse it to obtain the current status #(you may use pathinfo/jobid/phase entry point to avoid XML parsing)
            dom = parseString(data)
            phaseElement = dom.getElementsByTagName('uws:phase')[0]
            phaseValueElement = phaseElement.firstChild
            phase = phaseValueElement.toxml()
            if self.verbose:
                print("  Gaia Status: " + phase + " Job ID: " + jobid + " Time: " + str(datetime.now()))

            # Check finished
            if phase == 'COMPLETED':
                break

            # wait and repeat
            time.sleep(0.2)
            connection.close()
        # Get results
        connection = httplib.HTTPSConnection(self.host, self.port)
        connection.request("GET", self.pathinfo + "/" + jobid + "/results/result")
        response = connection.getresponse()
        data = response.read().decode('iso-8859-1')
        return json.loads(data)

    def request_job(self, query_text: str):
        # Create job
        params = urllib.urlencode({
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": "json",
            "PHASE": "RUN",
            "JOBNAME": "Any name (optional)",
            "JOBDESCRIPTION": "Any description (optional)",
            "QUERY": query_text,
        })
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        connection = httplib.HTTPSConnection(self.host, self.port)
        connection.request("POST", self.pathinfo, params, headers)
        # Status
        response = connection.getresponse()
        # Server job location (URL)
        location = response.getheader("location")
        # Jobid
        jobid = location[location.rfind('/') + 1:]
        if self.verbose:
            print("Gaia Batch Query - Job id: " + jobid)
        connection.close()
        return self.wait_for_job(jobid)

    def process_job(self, raw_results, dr_num=2):
        metadata = raw_results['metadata']
        data_names = [param_dict['name'] for param_dict in metadata]
        requested_names = {param_name for param_name in data_names if param_name in self.get_query_params(dr_num=dr_num)}
        data = [{key: value for key, value in zip(data_names, data_row) if key in requested_names and value is not None}
                for data_row in raw_results['data']]
        sources_dict = {}
        for params_dict in data:
            found_params = set(params_dict.keys()) & requested_names
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
            sources_dict[params_dict['source_id']] = params_dict
        return sources_dict

    def query_source(self, simbad_formatted_name_list, dr_num=2):
        list_of_sub_lists = []
        sub_list = []
        cut_name_list = [gaia_name[self.cut_index:] for gaia_name in simbad_formatted_name_list]
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
                query_text = f"""SELECT * 
                                 FROM gaiadr{dr_num}.gaia_source AS g, external.gaiadr2_geometric_distance AS d 
                                 WHERE {' OR '.join([f'(source_id={source_id} AND d.source_id = g.source_id)' for source_id in sub_list])};"""
            else:
                query_text = f"""SELECT {', '.join(list(self.get_query_params(dr_num=dr_num)))}
                                 FROM gaiadr{dr_num}.gaia_source 
                                 WHERE {' OR '.join([f'source_id={source_id}' for source_id in sub_list])};"""
            sources_dict = self.process_job(raw_results=self.request_job(query_text), dr_num=dr_num)
            self.star_dict.update({gaia_id_int: sources_dict[gaia_id_int] for gaia_id_int in sources_dict.keys()})


if __name__ == '__main__':
    g = GaiaQuery(verbose=True)
    g.query_source(simbad_formatted_name_list=['Gaia DR3 2308678825796092800'], dr_num=3)
    print(g.star_dict)