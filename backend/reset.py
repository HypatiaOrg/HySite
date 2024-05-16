import os
import time
from hypatia.config import ref_dir
from hypatia.database.gaia import GaiaLib
from standard_lib import standard_output
from hypatia.analyze.sorting import NatCat
from hypatia.tools.cat_file_ops import CatOps
from hypatia.database.tic.ops import tic_collection
from hypatia.database.simbad.ops import star_collection
from new_catalog import unique_abundances, insert_new_catalogs, new_catalogs_file_name, new_abundances_dir


def trash_auto_ref_files():
    star_collection.reset()
    gaia_lib = GaiaLib(verbose=True)
    for dr_number in gaia_lib.dr_numbers:
        if os.path.exists(gaia_lib.__getattribute__("gaiadr" + str(dr_number) + "_ref").ref_file):
            os.remove(gaia_lib.__getattribute__("gaiadr" + str(dr_number) + "_ref").ref_file)
    tic_collection.reset()


def reset_input_catalogs(verbose: bool = True):
    """
    This takes the entries in the catalog_file.csv, strips all the processing keywords like "raw" and "unique"
    and reestablishes the reference to the original unprocessed catalog file. All the catalog data the original
    unprocessed data is then moved to the new_data folder inside the abundance folder to be reprocessed.
    The handles for the catalog data are saved in the new_catalog_file.csv, ready for processing from scratch.
    The catalog_file.csv is then deleted.

    :param verbose: bool - when True, the code with report the actions it is taking.
    :return:
    """
    co = CatOps(cat_file=os.path.join(ref_dir, "catalog_file.csv"), load=True, verbose=verbose)
    co.reset_cat_file(reset_cat_file_name=new_catalogs_file_name, delete_old_cat_file=True, delete_and_move=True)


def full_reset_loop(verbose: bool = True):
    """
    The last comparability check for updates and bug fixes test is to fully reset all the hypatia data
    and reference files.

    In the case of an error during this definition, simply restart this definition. I file is use to keep track of
    what the code has completed, so you will not start over at the beginning, unless it brok on the fist step
    new_catalogs.py file.

    :param verbose: bool - If you are lonely, turn this to True to get teh code to tell you what it is doing.
    :return:
    """
    reset_file_name = os.path.join(ref_dir, 'reset_file.txt')
    completed_steps = set()
    if os.path.exists(reset_file_name):
        with open(reset_file_name, 'r') as f:
            for a_line in f.readlines():
                completed_steps.add(a_line.strip())

    if "trash_ref_files" not in completed_steps:
        # trash the reference files, Simbad, Gaia DR1, Gaia DR2, and TIC
        trash_auto_ref_files()
        with open(reset_file_name, 'w') as f:
            f.write("trash_ref_files\n")
    if "reset_input_catalogs" not in completed_steps:
        # move all the abundance catalogs to the new data folder, delete the unique abundances, keeps the original files
        reset_input_catalogs()
        with open(reset_file_name, 'a') as f:
            f.write("reset_input_catalogs\n")
    if "unique_abundances" not in completed_steps:
        # split the catalog files with multiple measurements of the same star, this also must get all the simbad data
        unique_abundances(verbose=verbose)
        with open(reset_file_name, 'a') as f:
            f.write("unique_abundances\n")
    if "exoplanet_names_update" not in completed_steps:
        # split the catalog files with multiple measurements of the same star, this also must get all the simbad data
        nat_cat = NatCat(params_list_for_stats=None,
                         star_types_for_stats=None,
                         catalogs_from_scratch=True,
                         verbose=verbose,
                         get_abundance_data=True,
                         get_exo_data=True,
                         refresh_exo_data=True,
                         catalogs_file_name=new_catalogs_file_name,
                         abundance_data_path=new_abundances_dir)
        with open(reset_file_name, 'a') as f:
            f.write("exoplanet_names_update\n")
    if "get_ref_data" not in completed_steps:
        # this does a faster update that gets the Gaia Data and TIC reference data.
        nat_cat = NatCat(params_list_for_stats=None,
                         star_types_for_stats=None,
                         catalogs_from_scratch=True,
                         verbose=verbose,
                         get_abundance_data=True,
                         get_exo_data=True,
                         refresh_exo_data=False,
                         fast_update_gaia=True,
                         catalogs_file_name=new_catalogs_file_name,
                         abundance_data_path=new_abundances_dir)
        with open(reset_file_name, 'a') as f:
            f.write("get_ref_data\n")
    # move the reference data in the main abundances folder and commit the file to the Git repository
    insert_new_catalogs(verbose=verbose, user_prompt=False)
    # when the process make it all the way, we delete the reset file
    os.remove(reset_file_name)
    # send out the standard output for inspection at the end of the loop.
    return standard_output(from_scratch=True, norm_key="lodders09")


def auto_restart(func, exceptions, tries=20, **kwargs):
    # try something
    for _ in range(tries):
        try:
            # This is the thing we actually want to complete
            output = func(kwargs)
        except exceptions:
            # if one of these happens we star the full reset loop over again.
            time.sleep(60)
        else:
            # if the try statement is completed, then this breaks the loop
            break
    else:
        # If the loop when all the why without hitting the "break",
        # we need to raise an exception to alert that the "function" in the "try" statement
        # never ran all the way through.
        raise TimeoutError("The maximum number of tries,", tries, "was exceeded. Something went terribly wrong.")
    return output


if __name__ == "__main__":
    from urllib3.exceptions import *
    from requests.exceptions import *
    # reset_input_catalogs()
    # trash_auto_ref_files()
    nat_cat, output_star_data = auto_restart(func=full_reset_loop,
                                             exceptions=(ConnectionError, ProtocolError),
                                             tries=20,
                                             verbose=True)
