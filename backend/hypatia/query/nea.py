import time
from typing import List
from urllib.request import urlretrieve

from hypatia.load.table_read import row_dict
from hypatia.tools.star_names import star_letters
from hypatia.database.name_db import get_star_data, get_main_id
from hypatia.config import (exoplanet_archive_filename, nea_exo_star_name_columns,
                            nea_unphysical_if_zero_params, nea_requested_data_types_default)


class ExoPlanet:
    def __init__(self, exo_data):
        [setattr(self, planet_param, exo_data[planet_param])
         for planet_param in set(exo_data.keys()) - nea_exo_star_name_columns
         if exo_data[planet_param] != ""
         and not (exo_data[planet_param] == 0 and planet_param in nea_unphysical_if_zero_params)
         and not (planet_param == "pl_orbeccen" and exo_data[planet_param] == 0 and exo_data["pl_orbeccen"] == 0)]
        self.planet_params = set(self.__dict__.keys())


class ExoPlanetHost:
    def __init__(self, exo_planets_dict):
        self.hypatia_handle = None
        self.simbad_doc = None
        self.main_star_id = None
        self.main_star_attr = None
        self.planet_letters = set()
        for pl_letter in exo_planets_dict.keys():
            self.__setattr__(pl_letter, ExoPlanet(exo_planets_dict[pl_letter]))
            self.planet_letters.add(pl_letter)

        # extract the star's names from the Exoplanet class and add those attributes to this class
        star_name_types = set()
        for planet_letter in self.planet_letters:
            star_name_types = nea_exo_star_name_columns & set(exo_planets_dict[planet_letter].keys())
            # these names are the small across all the exoplanet letters.
            break
        for exo_star_name in star_name_types:
            if exo_planets_dict[planet_letter][exo_star_name] != "":
                self.simbad_doc = get_star_data(exo_planets_dict[planet_letter][exo_star_name], test_origin="nea")
                self.main_star_id = self.simbad_doc["_id"]
                self.main_star_attr = self.simbad_doc["attr_name"]
                break
        else:
            raise KeyError("No star name found in the exoplanet data.")

        # extract this star's parameters (radius, mass, distance associated errors) and add to this class
        stellar_params = {}
        for planet_letter in self.planet_letters:
            stellar_params_this_star = {param for param in self.__getattribute__(planet_letter).planet_params
                                        if param[:3] == "st_"}
            # make the stellar parameters dictionary
            for param in stellar_params_this_star - set(stellar_params.keys()):
                stellar_params[param] = self.__getattribute__(planet_letter).__getattribute__(param)
            # remove the stellar attributes from the planet class.
            [delattr(self.__getattribute__(planet_letter), param) for param in stellar_params_this_star]
            [self.__getattribute__(planet_letter).planet_params.remove(param) for param in stellar_params_this_star]
        # set the stellar attributes to this class if they are not zero, which is unphysical for mass, radius, dist
        for param in stellar_params.keys():
            value = stellar_params[param]
            if value != 0:
                self.__setattr__(param, value)


class AllExoPlanets:
    def __init__(self,
                 requested_data_types: List[str] = None,
                 refresh_data: bool = True,
                 verbose: bool = True,
                 ref_star_names_from_scratch: bool = True):
        if requested_data_types is None:
            requested_data_types = nea_requested_data_types_default
        self.requested_data_types = requested_data_types
        self.verbose = verbose
        self.ref_star_names_from_scratch = ref_star_names_from_scratch
        self.exo_ref_file = exoplanet_archive_filename
        if refresh_data:
            if self.verbose:
                print("  Getting the freshest exoplanet data!")
            self.refresh_ref()
            self.data_is_fresh = True
            time.sleep(1)
            if self.verbose:
                print("    ...data received.")
        else:
            self.data_is_fresh = False
            if self.verbose:
                print("  Using existing exoplanet data on the local machine.")
        if self.verbose:
            print("  Loading exoplanet data...")
        self.single_name_stars = None
        self.multi_name_stars = None
        self.refresh_simbad_ref_data = False
        raw_exo = row_dict(self.exo_ref_file, key="hostname", delimiter=",", inner_key_remove=True)
        self.exo_host_names = set()
        non_host_names = set(raw_exo.keys) - {"pl_letter"}
        data_by_host_name = {}
        for nea_star_name in sorted(raw_exo.keys()):
            nea_row = raw_exo[nea_star_name]
            pl_letter = raw_exo['pl_letter']
            data_line_dict = {key: nea_row[key] for key in non_host_names}
            if nea_star_name in data_by_host_name:
                data_by_host_name[nea_star_name][pl_letter] = data_line_dict
            else:
                data_by_host_name[nea_star_name] = {pl_letter: data_line_dict}
        self.main_id_to_attr = {}
        for host_name in data_by_host_name.keys():
            data_by_host_name = data_by_host_name[host_name]
            exo_host = ExoPlanetHost(data_by_host_name)
            self.exo_host_names.add(exo_host.main_star_id)
            setattr(self, exo_host.main_star_attr, exo_host)
            self.main_id_to_attr[exo_host.main_star_id] = exo_host.main_star_attr

        self.exo_letters = self.check_for_new_star_letters()
        self.load_reference_host_names()
        if verbose:
            print("    Exoplanet data is ready.")

    def refresh_ref(self):
        items_str = ",".join(self.requested_data_types)
        # future work: upgraded to use new query standard:
        # <https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html>
        query_str = f'https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+{items_str}' +\
                    f'+from+ps&format=csv'

        urlretrieve(query_str, self.exo_ref_file)

    def check_for_new_star_letters(self):
        exo_letters = set()
        [[exo_letters.add(letter) for letter in self.__getattribute__(star_name).planet_letters]
         for star_name in self.exo_host_names]
        if exo_letters - star_letters != set():
            raise KeyError("Update needed for the star_letters in autostar.config.default_star_names.py to " +
                           "include the new exoplanet letters: " +
                           str(exo_letters - star_letters))
        return exo_letters

    def find_single_name_stars(self):
        self.single_name_stars = [xo.__getattribute__(star_name) for star_name in xo.exo_host_names
                                  if len(xo.__getattribute__(star_name).star_names) < 2]

    def find_multi_name_stars(self):
        self.multi_name_stars = [xo.__getattribute__(star_name) for star_name in xo.exo_host_names
                                 if len(xo.__getattribute__(star_name).star_names) > 1]

    def inspect(self):
        self.find_multi_name_stars()
        self.find_single_name_stars()
        print("Number of multi named stars:", len(self.multi_name_stars), " single named:", len(self.single_name_stars),
              '\nratio:', float(len(self.single_name_stars)) / float(len(self.multi_name_stars)))

    def load_reference_host_names(self):
        if self.verbose:
            print("  Getting Simbad names for exoplanet host stars...")
        len_host = len(self.exo_host_names)
        report_bin = int(len_host / 20)
        for index, host_name in enumerate(sorted(self.exo_host_names)):
            if self.verbose and index % report_bin == 0:
                print(f"      Getting name info for star: {host_name:30} {index + 1:5}, of {len_host:5}")

        if self.verbose:
            print("    Exoplanet name data updated to include star names from Simbad")

    def get_data_from_star_name(self, star_name: str, test_origin: str = "unknown"):
        # use simbad references to find what the hypatia_handle for this star should be
        man_star_id = get_main_id(star_name, test_origin=test_origin)
        if man_star_id in self.exo_host_names:
            return self.__getattribute__(self.main_id_to_attr[man_star_id])
        else:
            if self.verbose:
                print(f"Star name {star_name} (hypatia_handle: {man_star_id}) not found in exoplanet data.")
            return None


if __name__ == "__main__":
    xo = AllExoPlanets(refresh_data=True, verbose=True, ref_star_names_from_scratch=True)
    # xo.inspect()
    xo.load_reference_host_names()
