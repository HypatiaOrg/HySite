"""
New catalog insertion into the Hypatia sources.

Data Formatting Instructions
In the new files to be inserted into the hypatia catalog are required to be formatted in the following ways.
1) The # symbol at the start of a line denotes that line is a comment line. Comments are passed into the
Hypatia Database accompanying the contents of the catalogs data.
2) There is expected to be a header row for each of the data's columns.
3) The columns with the names of the stars should have a name like 'star' or 'star'. This column can also be named "hd"
or "hip" or any other Hypatia Database name type when the star names are of the same type.
4) The rest of the columns are for element abundance reported in dex notation on a scale from -inf-12.
5) Elemental abundance headers should be formatted using standard element abbreviations.
6) Header requirements for elemental abundance columns. Examples: CaH, CaIH, CaIIH, AF, ASi, SiNLTE
    a) Elements that are ratios are expected to be ratios of either Hydrogen "H" or Iron "Fe" at
       the end of the header string.
    b) Absolute abundances are expected to have an "A" at the start of the header string.
    c) NLTE abundances must have "NLTE" in the header string.
    d) Columns of all the above types are Allowed in the same file.
    e) Header strings with no "A", "H", or "Fe" flag are assumed to be ratios of hydrogen.
    f) no space character " ", underlines "_", or any character to separate flags and elements.
    g) Neutral elements can include a "I" roman numeral after the element abbreviation,
       ionized elements must include a roman numeral indicating their ionization state.
       No ionization flags are allowed for the denominator of the elemental ratios i.e. "H" and "Fe".
7) Abundance data that is missing in the table can be doted by an empty string or any number of
   whitespaces " ", "   ", ect.
8) Use commas "," or "|" for all delimiters for the header and data. Name the file with the ".csv" or ".tsv" suffix
   respectively.

Things to check when processing new data files:
1) Not all headers are properly annotated to indicate whether neutral or ionized lines were used. Therefore,
the line lists within the papers must be cross matched to make sure the data is cited correctly. In addition, it is
important to make sure that all major solar normalizations (Lodders, Asplund, Grevesse, Anders, etc.) have values
for the ionized element. If not, create a new column and use the same value as the neutral element.
2) Solar normalizations need to found for each reference. If a paper uses line-by-line differential analysis with
respect to the Sun, then the appropriate solar normalization is asplund09 (via personal communications with members
of the community).
3) If a dataset provides both [X/H] and A(X), preferentially use [X/H] (as long as there is a solar abundance) since
absolute abundances won't be included when the "internal" normalization is chosen.

Requirements for references and file locations:
1) All Files catalog files to be inserted into the Hypatia Database should be in the the folder
hypatia/load/abundance_data/new_data/
2) Filenames should be lowercase with no white space characters " ".
3) All catalogs to be inserted into the hypatia catalog should have all the required details listed in
hypatia/load/abundance_data/new_data/new_catalogs_file.csv. The file, new_catalogs_file.csv, contains
the information needed to find the filename, a reference for citation, and a reference for the data's
current normalization. The header of this fill will always be "short,long,norm". An example of a correctly
formatted row is "adamow14,Adamow et al. (2014),adamow14"
    a) The 'short' column is for a catalog's is the filename without the ".csv" extension. It is important
       that this name have no underscores "_" in the name at the start of processing. Underscores are
       added to the name as result of this processing, and the underscore is used as a flag to undo the
       processing if that needed at a later time.
    b) The 'long' column is a citation for the catalog. There are length restrictions, but do not use commmas
       to separate multiple references or years -- use a semicolon. No quotes needed. Also, put parentheses around
       the publication year for the front-end website processing.
    c) The 'norm' column is for a reference to the normalization for the data. All available normalizations
       are listed in the file hypatia/load/reference_data/solar_norm_ref.csv. The first column of this file
       contains the normalization handle that you must include for each catalog in the 'norm' column. If a
       catalog is purely absolute, write "absolute" for the solar normalization.

        Be Careful: Use the correct normalization or make a new reference row in
        hypatia/load/reference_data/solar_norm_ref.csv if needed. If a normalization value is missing that
        is used in the Elemental Abundances of a catalog being inserted, that data will not be able to be
        processed into the Hypatia Database.


The dex scale of the abundance data.
The data itself is expected to be in dex notation, a logarithmic scale. The abundance data for an element,
for example carbon "C", is often normalized to amount of hydrogen in a star. This example is taken from documentation in
hypatia.load.solar_norm.py. Below we see an example of what the dex notation means for stars normalized to hydrogen.
Other examples are found for "Fe" ratios abundance ratios and Absolute abundance notation and normalization
are found in hypatia.load.solar_norm.py.

    We take the relative value of an element X to Hydrogen (H) of a star compared to the solar abundance of the same
    ratio. Note the this calculation takes place in Log base 10 space, and returns values in log space, so simple
    additions and subtractions are all that is needed for this calculation.

    The abundance of Hydrogen, H_star, is defined as 10^12 atoms thus log(H_star) = log(10^12) = 12. By this definition,
    H_solar := log(10^12) = 12 and H_star := log(10^12) = 12 thus H_star = H_solar

    All other abundances are compared to that value. For a given elements X if may hav 10^6 atoms per 10^12 hydrogen
    atoms. Thus, the absolute abundance of element X is reported as log(X_star) = log(10^6) = 6. Since Hydrogen is the
    most abundant element for any star each the reported elemental abundance will be in the range of
    [12, -inf] = [log(10^12), log(0)].
"""
import os
import sys
import shutil

from hypatia.pipeline.nat_cat import NatCat
from hypatia.sources.catalogs.ops import CatOps
from hypatia.sources.catalogs.solar_norm import SolarNorm
from hypatia.sources.catalogs.catalogs import get_catalogs
from hypatia.configs.file_paths import (abundance_dir, ref_dir, new_abundances_dir, new_catalogs_file_name,
                                        default_catalog_file)


def load_catalogs(verbose=True):
    catalog_dict = get_catalogs(from_scratch=True,
                                local_abundance_dir=new_abundances_dir,
                                catalogs_file_name=new_catalogs_file_name,
                                verbose=verbose)
    return catalog_dict


def unique_abundances(verbose=True):
    """
    If there are double stars listed in one file, then the file gets split into multiples via this
    function.

    This function will need to be rerun if the root data file needs to be edited it. In this way,
    the changes will be propagated to the multiple files of unique star names that this file creates
    """
    if verbose:
        print("Checking stellar abundance catalog files to ensure each row entry is a unique star.\n" +
              "Some catalogs will have two entries for BD+74 595 and HIP 72607 even though those \n"
              "names refer to the same object.\n")
    catalog_dict = load_catalogs(verbose=verbose)
    for short_name in catalog_dict.keys():
        single_cat = catalog_dict[short_name]
        single_cat.find_double_listed()
        if len(single_cat.unique_star_groups) > 1:
            single_cat.write_catalog(output_dir=new_abundances_dir, target='unique', update_catalog_list=True)
        else:
            single_cat.write_catalog(output_dir=new_abundances_dir, target='raw', update_catalog_list=True)
    if verbose:
        print("catalogs have been checked, and when necessary split, to have each catalog file \n" +
              "have only one entry per unique star.\n")


def reset_input_catalogs(verbose: bool = True, reset_default_file: bool = False):
    """
    This takes the entries in the catalog_file.csv, strips all the processing keywords like "raw" and "unique"
    and reestablishes the reference to the original unprocessed catalog file. All the catalog data the original
    unprocessed data is then moved to the new_data folder inside the abundance folder to be reprocessed.
    The handles for the catalog data are saved in the new_catalog_file.csv, ready for processing from scratch.
    The catalog_file.csv is then deleted.

    :param verbose: bool - when True, the code with report the actions it is taking.
    :param reset_default_file: bool - when True, the default catalog file is deleted and the new_catalog_file.csv
                                      is used as the new catalog file. All processing steps are removed from the
                                      and the original data is moved to the new_data folder
                                      when False, the new_catalog_file.csv is used as the new catalog file.
                                      the data stays in the new data folder,
                                      and the files created by proces steps are removed.
    :return:
    """
    if reset_default_file:
        co = CatOps(cat_file=default_catalog_file, abundance_dir_for_reset=abundance_dir, verbose=verbose)
    else:
        co = CatOps(cat_file=new_catalogs_file_name, abundance_dir_for_reset=new_abundances_dir, verbose=verbose)
    co.reset_cat_file()


def insert_new_catalogs(verbose=True, user_prompt=True):
    if (not user_prompt) or input("Insert New Catalogs into Hypatia Database (y/n)?").lower() \
            in {True, "true", "yes", 'y'}:
        if verbose:
            print("\nUpdating main the main Hypatia Database with the following catalogs:")
        if not os.path.exists(default_catalog_file):
            with open(default_catalog_file, 'w') as f:
                f.write("short,long,norm\n")
        main_cat = CatOps(cat_file=default_catalog_file, verbose=verbose)
        new_cat = CatOps(cat_file=new_catalogs_file_name, verbose=verbose)
        if not new_cat.cat_dict.keys():
            raise Exception(f'No catalogs listed in the new_catalogs_file_name: {new_catalogs_file_name}')
        if verbose:
            for short_name in new_cat.cat_dict.keys():
                print("   ", short_name)
            print("")
        # check for catalog names that might be overwritten
        files_to_overwrite = set(main_cat.cat_dict.keys()) & set(new_cat.cat_dict.keys())
        if files_to_overwrite != set():
            print(files_to_overwrite)
            if input("Overwrite the catalog file for the " + str(len(files_to_overwrite)) +
                     " catalog handles listed above (y/n)?").lower() \
                in {False, "false", "no", 'n'}:
                sys.exit()
        # write update the file with the new names and write out
        main_cat.cat_dict.update(new_cat.cat_dict)
        main_cat.write()
        # move the formatted files.
        for short in new_cat.cat_dict.keys():
            extension = None
            if os.path.exists(os.path.join(new_abundances_dir, short + ".csv")):
                extension = ".csv"
            elif os.path.lexists(os.path.join(new_abundances_dir, short + ".tsv")):
                extension = ".tsv"
            shutil.move(os.path.join(new_abundances_dir, short + extension),
                        os.path.join(abundance_dir, short + extension))
            # add the new files to the git repository
            os.system("git add " + os.path.join(abundance_dir, short + extension))
            # move the original files and add them to the git repository as well
            base_name, *_ = short.split('_')
            base_extension = None
            if os.path.lexists(os.path.join(new_abundances_dir, base_name + ".csv")):
                base_extension = ".csv"
            elif os.path.lexists(os.path.join(new_abundances_dir, base_name + ".tsv")):
                base_extension = ".tsv"
            if base_extension is not None:
                shutil.move(os.path.join(new_abundances_dir, base_name + base_extension),
                            os.path.join(abundance_dir, base_name + base_extension))
                os.system("git add " + os.path.join(abundance_dir, base_name + base_extension))
        # delete some of the files that were fist processes as "raw" and then processed to "unique"
        [os.remove(os.path.join(new_abundances_dir, f)) for f in os.listdir(new_abundances_dir)
         if os.path.isfile(os.path.join(new_abundances_dir, f)) and '_raw_' in f]
        # clear the entry file to be fresh again.
        with open(new_catalogs_file_name, "w") as f:
            f.write("short,long,norm\n")
        if verbose:
            print("\nFile transfer completed. Files added to main catalog file\n" +
                  "and added to the local git repository.")
    else:
        print("  file transfer cancelled.")


if __name__ == "__main__":
    verbose = True
    reset_catalogs = False
    add_norm = False  # you only need to do one time, multiple times overwrites the previous entry. Also running will exit code 0.
    uniquify = True
    do_exo = False
    test_catalog = False
    insert_new = True

    # when done with upload, double-check that weird elements or new ionizations have representative error:
    # HySite/backend/hypatia/HyData/site_data

    if reset_catalogs:
        reset_input_catalogs(verbose, reset_default_file=False)

    elif add_norm:
        sn = SolarNorm(os.path.join(ref_dir, "solar_norm_ref.csv"))
        sn.add_normalization(handle="lucertini25", author="Baburaj et al.", year=2025, element_dict={"Na": 6.30, "Mg": 7.54, "Al": 6.47, "Si": 7.52, "S": 7.16, "Ca": 6.33, "Sc": 3.10, "ScII": 3.10, "Ti": 4.90, "TiII": 4.90, "V": 4.00, "VII": 4.00, "Cr": 5.64, "CrII": 5.64, "Mn": 5.37, "MnII": 5.37, "Fe": 7.52, "Co": 4.92, "Ni": 6.23, "Cu":4.21, "Zn": 4.62, "Rb": 2.60, "Sr": 2.92, "YII": 2.21, "ZrII": 2.58, "LaII": 1.14, "CeII": 1.61, "PrII": 0.76, "NdII": 1.45, "SmII": 1.00, "EuII": 0.52, "BaII": 2.17})
        #sn.add_normalization(handle="alexeeva23", author="Alexeeva et al.", year=2023, element_dict={"Fe":7.50, "Y":2.21})
        #sn.add_normalization(handle="pozhath24", author="Pozhath and Lambert", year=2024, element_dict={"Na":6.27, "Mg":7.59, "Al":6.37, "Si":7.52, "Ca":6.28, "ScII":3.16, "Ti":4.87, "TiII":4.98, "V":3.83, "Cr":5.59, "Mn":5.39, "Fe":7.44, "Co":4.81, "Ni":6.22, "Zn":4.50, "YII":2.16, "Zr":2.59, "BaII":2.24, "LaII":1.19, "NdII":1.40, "EuII":0.53})
        #sn.add_normalization(handle="spite22-24", author="Spite et al.", year=2022, element_dict={"Fe": 7.50, "C":8.50, "N":7.86, "O":8.76, "Na":6.30, "Mg":7.54, "Al":6.47, "Si":7.52, "Ca":6.33, "Sc":3.10, "Ti":4.90, "Cr":5.64, "Mn":5.37, "Co":4.92, "Ni":6.23, "Zn":4.62, "SrII":2.92, "YII":2.21, "ZrII":2.58, "Mo":192, "Ru":1.84, "Pd":1.66, "Ag":0.94, "BaII":2.17, "LaII":1.14, "CeII":1.60, "NdII":1.45, "EuII":0.52, "DyII":1.14, "ErII":0.96, "YbII":0.86})
        sn.write(os.path.join(ref_dir, "solar_norm_ref.csv"))
        print("New normalizations added to the solar_norm_ref.csv file.")
        print("exiting so that the file can be reloaded.")
        sys.exit()

    else:
        if uniquify:
            unique_abundances(verbose=verbose)

        if test_catalog:
            nat_cat = NatCat(params_list_for_stats=None,
                             star_types_for_stats=None,
                             catalogs_from_scratch=True,
                             verbose=verbose,
                             get_abundance_data=True,
                             get_exo_data=do_exo,
                             refresh_exo_data=do_exo,
                             fast_update_gaia=True,
                             catalogs_file_name=new_catalogs_file_name,
                             abundance_data_path=new_abundances_dir)

            dist_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                                        parameter_bound_filter=[('dist', 0, 500), ("Teff", 2300.0, 7500.)],
                                                        star_data_stats=True,
                                                        reduce_abundances=True)

            exo_output = nat_cat.make_output_star_data(min_catalog_count=1,
                                                       parameter_bound_filter=None,
                                                       has_exoplanet=True,
                                                       star_data_stats=True,
                                                       reduce_abundances=True)

            output_star_data = dist_output + exo_output
            output_star_data.normalize(norm_keys=["lodders09"])
            stats = output_star_data.stats

        elif insert_new:
            insert_new_catalogs(verbose=verbose, user_prompt=True)
