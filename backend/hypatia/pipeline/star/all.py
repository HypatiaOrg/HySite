import os
import hashlib
import datetime

import numpy as np

from hypatia.elements import element_rank
from hypatia.sources.gaia.ops import GaiaLib
from hypatia.config import star_data_output_dir
from hypatia.plots.histograms import simple_hist
from hypatia.plots.quick_plots import quick_plotter
from hypatia.pipeline.star.single import SingleStar
from hypatia.pipeline.star.stats import StarDataStats
from hypatia.object_params import StarDict, SingleParam
from hypatia.sources.catalogs.solar_norm import iron_id, iron_set
from hypatia.sources.nea.ops import get_all_nea, refresh_nea_data
from hypatia.sources.simbad.ops import get_star_data, get_main_id


def params_check(params_dict, hypatia_handle):
    star_name_str = f'Hypatia Handle: {hypatia_handle}'
    for params_key in params_dict.keys():
        if params_key != params_key.lower():
            raise KeyError(f'{star_name_str} The parameter Key {params_key} is not lowercase as required.')
        single_param = params_dict[params_key]
        if not isinstance(single_param, SingleParam):
            raise ValueError(f'{star_name_str} The parameter {params_key} is a SingleParam object, ' +
                             f'it is a {single_param} which is not allowed.')


class AllStarData:
    batch_len = 500
    non_abundance_keys = {'star_names', "main_id", "simbad_doc", 'original_star_names'}
    name_types_for_output = ["hip", "hd", "bd", "2MASS", "Gaia DR2", "TYC"]
    hydrogen_element_lower = {'bh', 'th', 'rh', 'h'}
    planet_output = [
        ("M_p", 'pl_mass', "(M_J)"),
        ("P", 'period', "(d)"),
        ("e", "eccentricity", ""),
        ('a', "semi_major_axis", "(AU)"),
    ]

    def __init__(self, verbose=True):
        self.verbose = verbose

        self.star_names = set()

        self.star_aliases = {}
        self.reverse_aliases = {}

        self.data_norms = set()

        self.stats = None

        self.stellar_params = None
        self.exoplanet_params = None
        self.available_abundance_catalogs = None
        self.available_abundances = None

        self.non_abundance_data_types = {'exo'}
        self.iron_el = iron_id
        self.iron_set = iron_set

        self.targets_requested = self.targets_found = self.targets_not_found = None

    def __iter__(self):
        for star_name in sorted(self.star_names):
            attr_name = get_star_data(test_name=star_name, test_origin="AllStarData.__iter__()")['attr_name']
            yield self.__getattribute__(attr_name)

    def get_abundances(self, all_catalogs):
        for short_catalog_name in sorted(all_catalogs.keys()):
            cat_data = all_catalogs[short_catalog_name]
            for catalog_dict, simbad_doc, main_id, original_star_name \
                    in zip(cat_data.abs_star_data, cat_data.star_docs,
                           cat_data.main_star_names, cat_data.original_star_names):
                catalog_dict["norm_key"] = all_catalogs[short_catalog_name].norm_key
                catalog_dict["long_name"] = all_catalogs[short_catalog_name].long_name
                catalog_dict['original_star_name'] = original_star_name
                catalog_dict['main_id'] = main_id
                # check to see if there is already an entry for this reference name
                attr_name = simbad_doc['attr_name']
                if main_id not in self.star_names:
                    # add this reference name to the set of names
                    self.star_names.add(main_id)
                    # create entry for the catalog information
                    self.__setattr__(attr_name, SingleStar(main_id, simbad_doc=simbad_doc, verbose=self.verbose))
                # get the default normalization
                self.__getattribute__(attr_name).add_abundance_catalog(short_catalog_name, catalog_dict)

    def get_exoplanets(self, refresh_exo_data: bool = False):
        if self.verbose:
            print('Loading and mapping all exoplanet data...')
        if refresh_exo_data:
            refresh_nea_data(verbose=self.verbose)
        for exo_host_doc in get_all_nea():
            star_main_id = exo_host_doc['_id']
            attr_name = exo_host_doc['attr_name']
            if star_main_id not in self.star_names:
                # add this reference name to the set of names
                self.star_names.add(star_main_id)
                # create entry for the catalog information
                self.__setattr__(attr_name, SingleStar(star_main_id,
                                                       get_star_data(test_name=star_main_id,
                                                                     test_origin="all_star_data"),
                                                       verbose=self.verbose))
            # get the default normalization
            self.__getattribute__(attr_name).add_exoplanet_data(exo_host_doc)

        if self.verbose:
            print("Exoplanet data acquired.\n")

    def get_targets(self, main_star_ids: list[str]):
        """
        This should be run last, after all the other data import methods, methods with the prefix 'get_' above.

        This method makes a star name entry for target stars that were not imported through other methods.
        Target stars that were found through other methods are modified to have the variable,
        SingleStar.is_target = True, set to True. This variable is used to define the set of target stars.
        :param main_star_ids: list - elements of this list each a str hypatia_handle.
        :return:
        """
        self.targets_requested = main_star_ids
        self.targets_found = set()
        self.targets_not_found = set()
        # See what stars are already load through other import processes.
        for hypatia_handle in main_star_ids:
            if hypatia_handle in self.star_names:
                self.targets_found.add(hypatia_handle)
            else:
                self.targets_not_found.add(hypatia_handle)
        # add the un_found stars to AllStarData
        for un_found_hypatia_handle in self.targets_not_found:
            simbad_doc = get_star_data(un_found_hypatia_handle)
            attr_name = simbad_doc['attr_name']
            main_star_id = simbad_doc['_id']
            # add this reference name to the set of names
            self.star_names.add(un_found_hypatia_handle)
            # create entry for the catalog information
            self.__setattr__(attr_name, SingleStar(main_star_id, simbad_doc, is_target=True, verbose=self.verbose))
        # note the found stars have been identified as target stars
        for found_hypatia_handle in self.targets_found:
            found_single_star = self.__getattribute__(found_hypatia_handle)
            found_single_star.is_target = True

    def fast_update_gaia(self):
        gaia_lib = GaiaLib(verbose=self.verbose)
        dr_number_to_string_names = StarDict()
        for star_name in self.star_names:
            simbad_doc = get_star_data(star_name)
            for dr_number in gaia_lib.dr_numbers:
                test_gaia_type_string = f"gaia dr{dr_number}"
                if test_gaia_type_string in simbad_doc.keys():
                    found_gaia_name = simbad_doc[test_gaia_type_string]
                    gaia_num = int(found_gaia_name.lower().replace(f'{test_gaia_type_string}', ""))
                    if gaia_lib.__getattribute__(f'gaiadr{dr_number}_ref').find(gaia_num) is None:
                        if dr_number not in dr_number_to_string_names.keys():
                            dr_number_to_string_names[dr_number] = set()
                        dr_number_to_string_names[dr_number].add(found_gaia_name)
        for dr_number, string_names in dr_number_to_string_names.items():
            number_of_names = len(string_names)
            finish_index = 0
            list_of_string_names = list(string_names)
            while finish_index < number_of_names:
                start_index = finish_index
                finish_index = min(number_of_names, finish_index + self.batch_len)
                gaia_lib.batch_update(simbad_formatted_names_list=list_of_string_names[start_index:finish_index],
                                      dr_number=dr_number)

    def do_stats(self, params_set=None, star_name_types=None):
        self.stats = StarDataStats(star_data=self,
                                   params_set=params_set, star_name_types=star_name_types)

    def reduce_elements(self):
        if self.verbose:
            print("Reducing elemental abundance data for Hypatia stars across that star's catalogs")
        for single_star in self:
            single_star.reduce()
        if self.verbose:
            print("  abundance reduction is complete.\n")

    def flat_database_output(self):
        now = datetime.datetime.now()
        file_name = os.path.join(star_data_output_dir, "hypatia_planetPrediction_")
        file_name += F"{'%02i' % now.day}_{'%02i' % now.month}_{'%04i' % now.year}_" \
                    + "norm" + 'lodders09'+ ".csv"
        column_header = "Name,X,Y,Z,Exo,Multi,MaxPMass,Fe,Li,C,O,Na,Mg,Al,Si,Ca,Sc,Ti,V,Cr,Mn,Co,Ni,Y1"
        elemlist = ["Fe", "Li", "C", "O", "Na", "Mg", "Al", "Si", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Co", "Ni", "Y"]
        plfile = open(file_name, 'w')
        plfile.write("%s\n" % column_header)

        for star_name in list(self.star_names):
            star_line = []
            star_line.append(self.__getattribute__(star_name).star_reference_name)
            if "exo" in self.__getattribute__(star_name).available_data_types:
                star_line.extend((1, len(self.__getattribute__(star_name).exo.planet_letters)))
                pmasses = []
                for planet_letter in sorted(self.__getattribute__(star_name).exo.planet_letters):
                    if "pl_bmassj" in self.__getattribute__(star_name).exo.__getattribute__(planet_letter).planet_params:
                        pmasses.append(self.__getattribute__(star_name).exo.__getattribute__(planet_letter).pl_bmassj)
                    else:
                        pmasses.append(0.)
                star_line.append(max(pmasses))
            else:
                star_line.append((0, 0, 0))
            for element in elemlist:
                if element in self.__getattribute__(star_name).reduced_abundances.available_abundances:
                    star_line.append(round(self.__getattribute__(star_name).reduced_abundances.__getattribute__(element).median, 2))
                else:
                    star_line.append("")
            star_line = str(star_line).replace('(', '').replace(')', '').strip('[').rstrip(']')
            plfile.write("%s\n" % star_line)

        plfile.close()

    def output_file(self, output_dir=None, exo_mode=False, do_absolute: bool = False):
        abs_output = False
        for norm_key in self.data_norms:
            if do_absolute:
                if abs_output:
                    continue
                else:
                    norm_key = "absolute"
            if output_dir is None:
                output_dir = star_data_output_dir
            file_name = os.path.join(output_dir, "hypatia_")
            if do_absolute:
                data_source_str = "from output_star_data.\n"
            else:
                data_source_str = "from star_data.\n"
            # Get today's date to mark the filename
            now = datetime.datetime.now()
            file_name += F"{'%04i' % now.year}_{'%02i' % now.month}_{'%02i' % now.day}_"
            if exo_mode:
                file_name += "exo_"
            if do_absolute:
                file_name += "absolute.txt"
            else:
                file_name += f"norm_{norm_key}.txt"
            if self.verbose:
                print("Writing the output file:", file_name)
                print("  " + data_source_str)
            output_dict = {}
            for single_star in self:
                simbad_doc = single_star.simbad_doc
                star_name_aliases = simbad_doc['aliases']
                attr_name = simbad_doc['attr_name']
                # A params formatting check add by Caleb Jan 2022
                params_this_star = single_star.params.available_params
                params_dict = {param: single_star.params.__getattribute__(param) for param in params_this_star}
                params_check(params_dict=params_dict, hypatia_handle=single_star.star_reference_name)
                # Main output name types.
                star_id = None
                if 'hip' in simbad_doc.keys():
                    try:
                        star_id = int(simbad_doc['hip'][3:])
                    except ValueError:
                        pass
                if star_id is None:
                    star_id = int(hashlib.md5(single_star.star_reference_name.encode()).hexdigest(), 16)
                star_write_lines = [f'Star: {star_id}']
                for name_type in self.name_types_for_output:
                    name_line = name_type + " = "
                    lower_case_name_type = name_type.lower()
                    if lower_case_name_type in simbad_doc.keys():
                        star_name = simbad_doc[lower_case_name_type]
                        if "2MASS" == name_type:
                            _, star_number = star_name.split("J", 1)
                            name_line += star_number
                        elif 'bd' == name_type:
                            name_line += "B" + star_name[2:]
                        elif 'Gaia DR2' == name_type:
                            name_line += star_name.replace("Gaia DR2 ", "")
                        else:
                            _, star_number = star_name.split(" ", 1)
                            if "hd" == name_type:
                                star_number = star_number.lstrip("0")
                            name_line += star_number
                    star_write_lines.append(name_line)
                # all the other available names
                star_write_lines.append("Other names: " + "|".join(star_name_aliases))
                # distance
                dist_line = 'dist (pc) = '
                if "dist" in params_this_star:
                    dist_line += str("%1.3f" % np.round(self.__getattribute__(attr_name).params.dist.value, decimals=3))
                star_write_lines.append(dist_line)
                # stellar_parameters
                for output_str, hypatia_param in [("RA", "raj2000"), ("Dec", "decj2000"),
                                                  ("RA proper motion", "pm_ra"), ("Dec proper motion", "pm_dec")]:
                    if hypatia_param in params_this_star:
                        value = str(single_star.params.__getattribute__(hypatia_param).value)
                    else:
                        value = ""
                    star_write_lines.append(output_str + " = " + value)
                # The position parameter:
                position_line = "Position = "
                if "x_pos" in params_this_star and "y_pos" in params_this_star and "z_pos" in params_this_star:
                    x = single_star.params.x_pos.value
                    y = single_star.params.y_pos.value
                    z = single_star.params.z_pos.value
                    position_line += F"[{'%1.3f' % np.around(x, decimals=3)}, {'%1.3f' % np.around(y, decimals=3)}, {'%1.3f' % np.around(z, decimals=3)}]"
                star_write_lines.append(position_line)
                # The UVW parameter
                uvw_line = "UVW = ("
                for a_letter in ["u_vel", "v_vel", "w_vel"]:
                    if a_letter in params_this_star:
                        uvw_line += str('%4.2f' % single_star.params.__getattribute__(a_letter).value)
                    else:
                        uvw_line += "9999.00"
                    if a_letter == "W_vel":
                        uvw_line += ")"
                    else:
                        uvw_line += ", "
                star_write_lines.append(uvw_line)
                # disk component
                disk_component_line = "Disk component: "
                if "disk" in params_this_star:
                    disk_component_line += str(single_star.params.disk.value)
                star_write_lines.append(disk_component_line)
                # more stellar parameters
                for output_str, hypatia_type in [("Spec Type", "sptype"), ("Teff", "teff"), ("logg", "logg"),
                                                 ("Vmag", "vmag"), ("Bmag", "bmag"), ("B-V", "bv")]:
                    output_line = output_str + " = "
                    if hypatia_type in params_this_star:
                        value = single_star.params.__getattribute__(hypatia_type).value
                        if isinstance(value, float):
                            output_line += F"{'%1.3f' % np.around(value, decimals=3)}"
                        else:
                            output_line += str(value)
                    star_write_lines.append(output_line)
                # stellar parameters
                for output_str, hypatia_type in [("mass (M_S)", 'mass'), ("radius (R_S)", 'rad')]:
                    output_line = output_str + " = "
                    if hypatia_type in params_this_star:
                        value = single_star.params.__getattribute__(hypatia_type).value
                        output_line += str(value)
                        error1_hypatia_type = hypatia_type + 'err1'
                        error2_hypatia_type = hypatia_type + 'err2'
                        if error1_hypatia_type in params_this_star or error2_hypatia_type in params_this_star:
                            output_line += " +- {"
                            if error1_hypatia_type in params_this_star:
                                output_line += str(single_star.params.__getattribute__(error1_hypatia_type).value)
                            output_line += ","
                            if error2_hypatia_type in params_this_star:
                                output_line += str(single_star.params.__getattribute__(error2_hypatia_type).value)
                            output_line += "}"
                    star_write_lines.append(output_line)
                # Exoplanets data
                if exo_mode and "exo" in single_star.available_data_types:
                    # number of planets
                    all_planets = single_star.exo['planets']
                    star_write_lines.append(f"Number of planets = {len(all_planets)}")
                    # exoplanet parameters
                    for planet_letter, planet_record in all_planets.items():
                        output_line = f"[{planet_letter}] "
                        planet_params = planet_record.get('planetary', None)
                        if planet_params is not None:
                            planet_params_rec = planet_params.to_record()
                            for output_str, planet_param, unit in self.planet_output:
                                if planet_param in planet_params_rec.keys():
                                    param_data = planet_params_rec[planet_param]
                                    output_line += f"{output_str} {param_data['value']}"
                                    output_line += " +- {"
                                    if 'err_low' in param_data.keys():
                                        output_line += str(param_data['err_low'])
                                    output_line += ","
                                    if "err_high" in param_data.keys():
                                        output_line += str(param_data['err_high'])
                                    output_line += "}"
                                output_line += unit + ", "
                            star_write_lines.append(output_line[:-2])
                # The elemental values
                for catalog in single_star.available_abundance_catalogs:
                    single_catalog = single_star.__getattribute__(catalog)
                    if norm_key == "absolute":
                        cat_location = single_catalog
                    else:
                        cat_location = single_catalog.__getattribute__(norm_key)
                    ordered_element_list = sorted(cat_location.available_abundances, key=element_rank)
                    for element in ordered_element_list:
                        if element.is_nlte:
                            continue
                        element_str = str(element)
                        element_value = np.around(cat_location.__getattribute__(element_str), decimals=3)
                        an_element_line = element_str.replace("_", "")
                        element_lower = element_str.strip().lower()
                        if element_lower in self.hydrogen_element_lower or element_lower[-1] != 'h':
                            an_element_line += "H"
                        an_element_line += f" {element_value} [{single_catalog.catalog_long_name}]"
                        star_write_lines.append(an_element_line)
                # there is a blank line between stars
                star_write_lines.append("")
                output_dict[attr_name] = star_write_lines
            if not os.path.isdir(os.path.dirname(file_name)):
                os.mkdir(os.path.dirname(file_name))
            # open the file to be written
            with open(file_name, 'w') as f:
                # put the preferred star name types at the top of the file.
                [[f.write(a_line + "\n") for a_line in write_lines] for write_lines in output_dict.values()]
            if do_absolute:
                abs_output = True

    def get_single_star_data(self, star_name):
        main_star_id = get_main_id(star_name)
        if main_star_id in self.star_names:
            simbad_doc = get_star_data(main_star_id, test_origin="AllStarData.get_single_star_data")
            return self.__getattribute__(simbad_doc['attr_name'])
        else:
            return None

    def find_available_attributes(self):
        if self.verbose:
            print("Finding available attributes for the class:", self.__class__.__name__)
        self.stellar_params = set()
        self.exoplanet_params = set()
        self.available_abundance_catalogs = set()
        self.available_abundances = set()
        for single_star in self:
            self.stellar_params |= single_star.params.available_params
            if "exo" in single_star.available_data_types:
                for planet_letter, single_planet in single_star.exo['planets'].items():
                    self.exoplanet_params |= set(single_planet.keys())
            self.available_abundance_catalogs |= single_star.available_abundance_catalogs
            for catalog_name in single_star.available_abundance_catalogs:
                available_abundances_this_star = single_star.__getattribute__(catalog_name).available_abundances
                self.available_abundances |= available_abundances_this_star
        if self.verbose:
            print("  Stellar Parameters Found:      ", sorted(self.stellar_params))
            print("  Exoplanet Parameters Found:    ", sorted(self.exoplanet_params))
            print("  Available Abundance Catalogs:  ", sorted(self.available_abundance_catalogs))
            print("  Available Elemental Abundances:", sorted(self.available_abundances, key=element_rank))
            print()

    def check_availability(self, thing):
        if any([self.stellar_params is None, self.exoplanet_params is None, self.available_abundance_catalogs is None,
                self.available_abundances is None]):
            self.find_available_attributes()
        if not any([thing in self.stellar_params, thing in self.exoplanet_params,
                    thing in self.available_abundance_catalogs, self.available_abundances]):
            raise KeyError(str(thing) + "  was not in any of the expected sets of key words.\n" +
                           "1) check spelling and letter case\n" +
                           "2) rerun the find_available_attributes method\n" +
                           "3) consider adding a new set to be collected by the find_available_attributes method")

    def thing_typing(self, thing, title):
        if thing in self.stellar_params:
            type_of_thing = "Stellar Parameter"
            title += "Stellar Parameter " + thing + ","
        elif thing in self.exoplanet_params:
            type_of_thing = "Exoplanet Parameter"
            title += "Exoplanet Parameter " + thing + ","
        elif thing in self.available_abundances:
            type_of_thing = "Stellar Abundance"
            title += "Stellar Abundance " + thing + ","
        else:
            raise KeyError(str(thing) + "  was not in any of the expected sets of key words.\n" +
                           "1) check spelling and letter case\n" +
                           "2) rerun the find_available_attributes method\n" +
                           "3) consider adding a new set to be interpreted by histogram_anything")
        return type_of_thing, title

    def histogram_anything(self, thing, bins=10, color="darkorange",  show=False, save=True):
        if self.verbose:
            print("Making a histogram for:", thing)
        self.check_availability(thing)
        x = []
        title = ""
        if thing in self.stellar_params:
            for star_name in self.star_names:
                single_star = self.__getattribute__(star_name)
                if thing in single_star.params.available_params:
                    value = single_star.params.__getattribute__(thing)
                    x.append(value)
            title += "Stellar Parameter " + thing

        elif thing in self.exoplanet_params:
            for star_name in self.star_names:
                single_star = self.__getattribute__(star_name)
                if "exo" in single_star.available_data_types:
                    for planet_letter in single_star.exo.planet_letters:
                        single_planet = single_star.exo.__getattribute__(planet_letter)
                        if thing in single_planet.planet_params:
                            x.append(single_planet.__getattribute__(thing))
            title += "Exoplanet Parameter " + thing
        elif thing in self.available_abundances:
            for star_name in self.star_names:
                single_star = self.__getattribute__(star_name)
                for catalog_name in single_star.available_abundance_catalogs:
                    available_abundances = single_star.__getattribute__(catalog_name).available_abundances
                    if thing in available_abundances:
                        value = single_star.__getattribute__(catalog_name).__getattribute__(thing)
                        x.append(value)
            title += "Stellar Abundance of " + thing
        else:
            raise KeyError(f"'{thing}' was not in any of the expected sets of key words.\n" +
                           "  1) check spelling and letter case\n" +
                           "  2) rerun the find_available_attributes method\n" +
                           "  3) consider adding a new set to be interpreted by histogram_anything")
        title += ", " + str(bins) + " bins"
        simple_hist(x=x, bins=bins, title=title, x_label=thing, y_label="counts", color=color, show=show, save=save)

    def xy_plot(self, x_thing, y_thing, color="darkorchid", show=False, save=True, do_pdf=True):
        if self.verbose:
            print("Making an XY plot for:", x_thing, "and", y_thing)
        self.check_availability(x_thing)
        self.check_availability(y_thing)
        plot_dict = {}
        x = []
        y = []
        title = ""
        x_type_of_thing, title = self.thing_typing(x_thing, title)
        y_type_of_thing, title = self.thing_typing(y_thing, title)
        title = title[:-1]

        for single_star in self:
            possible_x_values = single_star.find_thing(thing=x_thing, type_of_thing=x_type_of_thing)
            possible_y_values = single_star.find_thing(thing=y_thing, type_of_thing=y_type_of_thing)
            if possible_x_values and possible_y_values:
                # possible x and y both have at least one value
                len_px = len(possible_x_values)
                len_py = len(possible_y_values)
                if len_px == len_py:
                    # possible x and y are the same length.
                    x.extend(possible_x_values)
                    y.extend(possible_y_values)
                elif len_px == 1:
                    # possible x is a singleton and y is longer
                    x.extend(possible_x_values * len_py)
                    y.extend(possible_y_values)
                elif len_py == 1:
                    # possible y is a singleton and x is longer
                    x.extend(possible_x_values)
                    y.extend(possible_y_values * len+len_px)

        plot_dict['verbose'] = self.verbose
        plot_dict['title'] = title
        plot_dict['xlabel'] = x_thing
        plot_dict['ylabel'] = y_thing
        plot_dict['plot_file_name'] = title.replace(" ", "_")
        plot_dict["show"] = show
        plot_dict['save'] = save
        plot_dict["do_pdf"] = do_pdf

        plot_dict['ls'] = "None"
        plot_dict['alpha'] = 0.2

        plot_dict["x_data"] = [np.array(x)]
        plot_dict["y_data"] = [np.array(y)]
        plot_dict['colors'] = [color]

        quick_plotter(plot_dict)
