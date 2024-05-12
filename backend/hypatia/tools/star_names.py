import os
from collections import namedtuple


print("Using Hypatia Catalogue Star Names")
# the directory the contains this file
star_names_dir = os.path.dirname(os.path.realpath(__file__))
star_letters = {"a", "b", "c", "d", 'e', "f", 'g', 'h', 'i', "s", "l", "n", "p"}
double_star_letters = {'ab', 'bc', "bb"}

single_part_star_names = {"hip", "hd", "hr", "ltt", "hic", "gj", "gaia", "gaia dr1", "gaia dr2", 'gaia dr3',
                          "[bhm2000]", "[bsd96]", "gv", "cvs", "mfjsh2", "ls", 'lhs',
                          'gcirs', 'sh2', 'pismis', 'plx', 'sb', 'pwm', '[s84]', "ic", "wasp", "ross", "koi",
                          "kepler", "hii", "corot", "tres", 'kic', "marvels", 'epic', 'azv', "bds", "k2", "kelt", 'toi',
                          "gl", 'qatar', "sweeps", "wts", "ph", "ngts", "trappist", "wolf", 'pds', "roxs",
                          "mascara", 'chxr', 'tap', "nsvs", "pots", "csv", "css", 'dmpp', 'ogle-tr',
                          "uscoctio",  "usco ctio", "usco", "wendelstein", "tic", "cfhtwir-oph", "yses", "coconuts",
                          "gpx", "nltt", "bpm"}
multi_part_star_names = {"bd", "cod", 'cd',  "cpd", "tyc", "g", "lp", "gsc", "ucac", 'ntts', 'iras', "htr",
                         "l", "ag", 'csi', "wd", 'lupus', 'bps cs', "bps bs", "bpscs", 'bpsbs', "cs", 'bs'}
string_names = {"2mass", "2masx", "apm", "asas", "bas", 'cl*berkeley', 'cl*collinder', 'cl*ic4651', 'cl*melotte',
                'clmelotte', 'cl melotte', 'cl*terzan', 'cl*trumpler', "ges", 'cmd', 'cl*ic', "sds", "hat", "hats",
                'v*', "*", "**", 'wise', 'ogle', "xo", "pmc", "wds", "ids", 'moa', "denis", "psr", 'kmt', "name", 'tcp',
                'em*', 'ukirt', "mxb", "vhs", "lspm", 'ngc', 'cl* ngc', '2massw', "rx", "psr", "he", "gaia", "2massi",
                'rave', 'lamost', 'ges', 'm'}

star_name_types = single_part_star_names | multi_part_star_names | string_names
names_that_are_listed_without_a_space_sometimes = {'bd', "cd"}

asterisk_names = {'gam', 'rho', 'ome', "tau", 'kap', 'ups', 'bet', "phi", 'omi', "psi", "eps", 'iot', "alf", "oph",
                  "ab", 'ci', 'dp', 'ct', 'dh', 'uz', "yz", "nu", "mu", "rr", 'xi', 'nn', "v830", 'de', 'ny', 'ds',
                  "hn", 'fu', "gu", 'gq', "uz", 'hw', 'hu', 'mic'}
asterisk_name_types = {'v*', "*", "**", 'em*', "Name"}


StarName = namedtuple("StarName", "type id")

# for sorting.py
star_name_preference = ["hip", 'gaia dr3', 'gaia dr2', 'gaia dr1', "hd", 'bd', "2mass", "tyc"]
star_name_preference.extend([star_name for star_name in sorted(star_name_types)
                             if star_name not in star_name_preference[:]])


def optimal_star_name(star_name_lower):
    # find the star's name_type
    try:
        name_type, *possible_name_types = [star_name_type for star_name_type in star_name_types
                                           if star_name_type == star_name_lower[:len(star_name_type)]]
    except ValueError:
        raise ValueError(F"No star names type matches for: {star_name_lower}")
    # This is a catch to make sure GL stars are not classified as G stars
    name_len = len(name_type)
    for possible_name_type in possible_name_types:
        if name_len < len(possible_name_type):
            name_len = len(possible_name_type)
            name_type = possible_name_type
    return name_type


def remove_key(d, key):
    r = dict(d)
    del r[key]
    return r


def star_letter_check(striped_name):
    star_letter = None
    if striped_name[-2:] in double_star_letters:
        star_letter = striped_name[-2:]
        remaining_star_id = striped_name[:-2]
    elif striped_name[-1] in star_letters:
        star_letter = striped_name[-1]
        remaining_star_id = striped_name[:-1]
    else:
        remaining_star_id = striped_name
    return remaining_star_id, star_letter


def one_part_star_names_format(star_name_lower, name_key):
    # format example (2310883 ,"a") or (2310883,)
    striped_name = star_name_lower.replace(name_key, "", 1)
    # single part star names are never negative values
    if "-" == striped_name[0]:
        striped_name = striped_name[1:]
    # check for star letters, i.e. 'a', 'b', 'c', and 'd'
    striped_name, found_star_letter = star_letter_check(striped_name)
    if found_star_letter is None:
        try:
            formatted_name = (int(striped_name),)
        except ValueError:
            formatted_name = striped_name.strip()
    else:
        try:
            formatted_name = (int(striped_name.replace(found_star_letter, "")), found_star_letter)
        except ValueError:
            formatted_name = (striped_name.strip().replace(found_star_letter, ""), found_star_letter)
    if name_key in {"usco ctio", "usco"}:
        name_key = "uscoctio"
    return StarName(name_key, formatted_name)


def split_no_space(a_string):
    an_int = int(a_string)
    # get rid of the '+' symbol
    a_string = str(an_int)
    if an_int < 0.0:
        return [a_string[:3], a_string[3:]]
    else:
        return [a_string[:2], a_string[2:]]


def multi_part_star_names_format(star_name_lower, name_key):
    # format example ((-13, 0872) ,"a") or (((-13, 0872)))
    striped_name = star_name_lower.replace(name_key, "", 1).strip()
    if name_key in {"cs", "bpscs"}:
        name_type = 'bps cs'
    elif name_key in {"bs", 'bpsbs'}:
        name_type = 'bps bs'
    else:
        name_type = name_key
    # check for star letters, i.e. 'a', 'b', 'c', and 'd'
    striped_name, found_star_letter = star_letter_check(striped_name)
    # plus minus zero star names check
    string_vector = []
    if name_key in {"bd", "ag", 'cd', "csi"}:
        if striped_name[0] == "-":
            string_vector.append("-")
            striped_name = striped_name[1:]
        elif striped_name[0] == "+":
            string_vector.append("+")
            striped_name = striped_name[1:]
        else:
            string_vector.append("+")
        if name_key in names_that_are_listed_without_a_space_sometimes and " " not in striped_name:
            string_vector.extend([striped_name[:2], striped_name[2:]])
        else:
            string_vector.extend(striped_name.split())
    else:
        # Check to see if the multipart star name is delimited by '-"
        if "-" in striped_name[1:]:
            striped_name = striped_name[0] + striped_name[1:].replace("-", " ")
        # Check to see if the multipart star name is delimited by '+"
        if "+" in striped_name[1:]:
            striped_name = striped_name[0] + striped_name[1:].replace("+", " ")
        # split the multi part star name.
        if " " in striped_name:
            string_vector = striped_name.split()
        else:
            if name_key in names_that_are_listed_without_a_space_sometimes:
                string_vector = split_no_space(striped_name)
            else:
                raise ValueError("The multipart string: " + star_name_lower + " can not be parsed")
    # turn the strings into ints
    num_vector = []
    for element in string_vector:
        try:
            num_vector.append(int(element))
        except ValueError:
            num_vector.append(element)
    # add any found star letters
    if found_star_letter is not None:
        num_vector.append(found_star_letter)
    # format and return the parsed hypatia name for a multi-part star.
    formatted_name = tuple(num_vector)
    return StarName(name_type, formatted_name)


def moa_format(stripped_of_name_type):
    split_name = stripped_of_name_type.split("-")
    if len(split_name) == 3:
        year, blg, number = split_name
        if blg[0] == "{":
            moa_string = year + "-" + blg[1:-1].upper() + "-" + number.strip()
        else:
            moa_string = year + "-" + blg.upper() + "-" + number.strip()
        if moa_string[-1] == "l":
            moa_string = moa_string[:-1].strip() + " L"
        moa_string = " " + moa_string
    elif len(split_name) == 2:
        thing, number = split_name
        moa_string = thing + "-"
        if "l" == number[-1]:
            moa_string += number[:-1].strip() + " {L}"
        else:
            moa_string += number.upper()
        moa_string = "-" + moa_string
    else:
        raise TypeError("MOA string not of the expected format for parsing: " + stripped_of_name_type)
    return moa_string


def string_star_name_format(star_name_lower, name_key):
    if name_key == star_name_lower[:len(name_key)]:
        stripped_of_name_type = star_name_lower[len(name_key):].strip()
    else:
        stripped_of_name_type = star_name_lower.strip()
    if "-" == stripped_of_name_type[0]:
        stripped_of_name_type = stripped_of_name_type[1:]
    stripped_of_name_type = stripped_of_name_type.strip()
    if name_key == "moa":
        stripped_of_name_type = moa_format(stripped_of_name_type)
    elif name_key == 'kmt' and stripped_of_name_type[-1] == "l":
        stripped_of_name_type = stripped_of_name_type[:-1]
    elif name_key == "ogle":
        if stripped_of_name_type[:2] == 'tr':
            stripped_of_name_type = stripped_of_name_type.replace("-", ' ')
    return StarName(name_key, stripped_of_name_type)


def star_name_format(star_name: str, key: str = None) -> tuple:
    star_name_lower = str(star_name).lower()
    if key is None:
        name_type = optimal_star_name(star_name_lower)
        # a catch for a few stars in the Adibekyan 12 catalog, and other formatting of CD stars
        if name_type == "cod":
            name_type = "cd"
            star_name_lower = star_name_lower.replace('cod', "cd")
        elif name_type == "clmelotte" or name_type == "cl*melotte":
            name_type = "cl melotte"+star_name_lower[11:]
    else:
        name_type = key
        """
        these are a bunch of catches for catalog specific formatting
        """
        if key == "bd":
            if star_name_lower[0] == "b" and star_name_lower[1] != "d":
                star_name_lower = star_name_lower.replace("b", "bd", 1)
        elif key == "cod":
            name_type = 'cd'
            if star_name_lower[0] == "c" and star_name_lower[1] != "o":
                star_name_lower = star_name_lower.replace("c", "cd", 1)
            else:
                star_name_lower = star_name_lower.replace("cod", "cd", 1)
        elif key == 'cd' and star_name_lower[0] == "c" and star_name_lower[1] != "d":
            star_name_lower = star_name_lower.replace("c", "cd", 1)
        elif key == "cpd" and star_name_lower[0] == "p":
            star_name_lower = star_name_lower.replace("p", "cpd", 1)
        elif key == '2mass' and star_name_lower[0] != 'j' and "2mass" != star_name_lower[:5]:
            star_name_lower = 'j' + star_name_lower
        elif key == 'hd' and "." in star_name_lower:
            star_name_lower, _ = star_name_lower.split('.')
    # test if the name is a single number or an ordered tuple
    if name_type in single_part_star_names:
        formatted_name = one_part_star_names_format(star_name_lower, name_type)
    elif name_type in multi_part_star_names:
        formatted_name = multi_part_star_names_format(star_name_lower, name_type)
    elif name_type in string_names:
        formatted_name = string_star_name_format(star_name_lower, name_type)
    else:
        raise NameError("The format of star_name: " + str(star_name) + " was not parsed.\n"
                        "It was not found in the set of star_name_types: " + str(star_name_types) + ".")
    return formatted_name


format_functions = {}

def string_name(func):
    name_type = func.__name__
    format_functions[name_type] = func
    return func


@string_name
def asterisk(star_id):
    return "* " + star_id


@string_name
def azv(star_id):
    if len(star_id) > 1:
        return "AzV " + str(star_id[0]) + star_id[1]
    else:
        return "AzV " + str(star_id[0])


@string_name
def bd(star_id):
    if len(star_id) > 3:
        return 'BD' + star_id[0] + str("%02i" % abs(star_id[1])) + " " + str("%05i" % star_id[2]) + star_id[3]
    else:
        return 'BD' + star_id[0] + str("%02i" % abs(star_id[1])) + " " + str("%05i" % star_id[2])

@string_name
def bds(star_id):
    if len(star_id) > 1:
        return 'BDS ' + str(star_id[0]) + star_id[1]
    else:
        return 'BDS ' + str(star_id[0])

@string_name
def bpm(star_id):
    if len(star_id) > 1:
        return 'BPM ' + str(star_id[0]) + star_id[1]
    else:
        return 'BPM ' + str(star_id[0])

@string_name
def bps_bs(string_id):
    return F"BPS BS {'%05i' % string_id[0]}-{'%04i' % string_id[1]}"


@string_name
def bps_cs(string_id):
    return F"BPS CS {'%05i' % string_id[0]}-{'%04i' % string_id[1]}"


@string_name
def chxr(star_id):
    if len(star_id) > 1:
        return 'CHXR ' + str(star_id[0]) + star_id[1]
    else:
        return 'CHXR ' + str(star_id[0])


@string_name
def cpd(star_id):
    if len(star_id) > 2:
        return "CPD" + str(star_id[0]) + " " + str("%05i" % star_id[1]) + star_id[2]
    else:
        return "CPD" + str(star_id[0]) + " " + str("%05i" % star_id[1])


@string_name
def cd(star_id):
    if len(star_id) > 3:
        return "CD" + star_id[0] + str("%02i" % abs(star_id[1])) + " " + str("%05i" % star_id[2]) + star_id[3]
    else:
        return "CD" + star_id[0] + str("%02i" % abs(star_id[1])) + " " + str("%05i" % star_id[2])

@string_name
def cfhtwir_oph(star_id):
    if len(star_id) < 2:
        return "CFHTWIR-Oph " + str("%05i" % star_id[0])
    else:
        return "CFHTWIR-Oph " + str("%05i" % star_id[0]) + star_id[1]


@string_name
def cl_ngc(star_id):
    return "Cl* NGC " + star_id

@string_name
def coconuts(star_id):
    if len(star_id) < 2:
        return "COCONUTS " + str("%05i" % star_id[0])
    else:
        return "COCONUTS " + str("%05i" % star_id[0]) + star_id[1]


@string_name
def cs(star_id):
    return "BPS CS " + str("%05i" % star_id[0]) + "-" + str("%04i" % star_id[1])


@string_name
def corot(star_id):
    if len(star_id) > 1:
        return "CoRoT-" + str("%02i" % star_id[0]) + star_id[1]
    else:
        if star_id[0] > 100:
            return "CoRoT " + str("%09i" % star_id[0])
        else:
            return "CoRoT-" + str("%02i" % star_id[0])


@string_name
def double_asterisk(star_id):
    return "** " + star_id


@string_name
def denis(star_id):
    return "DENIS " + star_id


@string_name
def dmpp(star_id):
    if len(star_id) > 1:
        return "DMPP-" + str(star_id[0]) + star_id[1]
    else:
        return "DMPP-" + str(star_id[0])


@string_name
def em_asterisk(star_id):
    return "EM* " + star_id


@string_name
def epic(star_id):
    if len(star_id) > 1:
        return 'EPIC ' + str(star_id[0]) + star_id[1]
    else:
        return 'EPIC ' + str(star_id[0])


@string_name
def g(star_id):
    if len(star_id) < 3:
        return "G " + str("%03i" % star_id[0]) + "-" + str("%03i" % star_id[1])
    else:
        return "G " + str("%03i" % star_id[0]) + "-" + str("%03i" % star_id[1]) + star_id[2]


@string_name
def gl(star_id):
    if isinstance(star_id, str):
        return "GL " + star_id
    if len(star_id) > 1:
        return 'GL ' + str(star_id[0]) + star_id[1]
    else:
        return 'GL ' + str(star_id[0])

@string_name
def gaia(star_id):
    return "Gaia" + str(star_id[0])

@string_name
def gaia_dr1(star_id):
    return "Gaia DR1 " + str(star_id[0])


@string_name
def gaia_dr2(star_id):
    return "Gaia DR2 " + str(star_id[0])


@string_name
def gaia_dr3(star_id):
    return "Gaia DR3 " + str(star_id[0])

@string_name
def ges(star_id):
    if star_id[0].lower() == "j":
        return "GES " + star_id.upper()
    else:
        return "GES J" + star_id

@string_name
def gj(star_id):
    string = "GJ "
    if type(star_id) == str and "." in star_id:
        string += str("%03.1f" % float(star_id))
    else:
        if type(star_id[0]) == str and "." in star_id[0]:
            string += str("%3.1f" % float(star_id[0]))
        else:
            string += str(star_id[0])
        if len(star_id) > 1:
            string += " " + star_id[1]
    return string

@string_name
def gpx(star_id):
    if len(star_id) > 1:
        return "GPX-" + str("%02i" % star_id[0]) + star_id[1]
    else:
        if star_id[0] > 100:
            return "GPX " + str("%09i" % star_id[0])
        else:
            return "GPX-" + str("%02i" % star_id[0])

@string_name
def gsc(star_id):
    return "GSC " + str("%05i" % star_id[0]) + "-" + str("%05i" % star_id[1])


@string_name
def gv(star_id):
    if len(star_id) > 1:
        return "GV " + str(star_id[0]) + star_id[1]
    else:
        return "GV " + str(star_id[0])


@string_name
def hat(star_id):
    return "HAT-" + star_id.upper()


@string_name
def hats(star_id):
    return "HATS-" + star_id.upper()


@string_name
def hd(star_id):
    if len(star_id) < 2:
        return "HD " + str("%06i" % star_id[0])
    elif type(star_id) == str:
        return "HD " + star_id
    else:
        return "HD " + str("%06i" % star_id[0]) + star_id[1]

@string_name
def he(star_id):
    return "HE " + star_id.upper()

@string_name
def hic(star_id):
    if len(star_id) < 2:
        return "HIC " + str("%05i" % star_id[0])
    else:
        return "HIC " + str("%05i" % star_id[0]) + star_id[1]


@string_name
def hip(star_id):
    if len(star_id) < 2:
        return "HIP " + str("%i" % star_id[0])
    else:
        return "HIP " + str("%i" % star_id[0]) + star_id[1]


@string_name
def hr(star_id):
    if len(star_id) < 2:
        return "HR " + str("%05i" % star_id[0])
    else:
        return "HR " + str("%05i" % star_id[0]) + star_id[1]


@string_name
def ic(star_id):
    return "IC " + star_id


@string_name
def ids(star_id):
    return "IDS " + star_id


@string_name
def k2(star_id):
    if len(star_id) < 2:
        return "K2-" + str(star_id[0])
    else:
        return "K2-" + str(star_id[0]) + star_id[1]


@string_name
def kelt(star_id):
    if len(star_id) < 2:
        return "KELT-" + str(star_id[0])
    else:
        return "KELT-" + str(star_id[0]) + star_id[1]


@string_name
def kepler(star_id):
    if len(star_id) < 2:
        return "Kepler-" + str(star_id[0])
    else:
        return "Kepler-" + str(star_id[0]) + star_id[1]


@string_name
def kic(star_id):
    return "KIC " + str('%08i' % star_id[0])


@string_name
def kmt(star_id):
    return "KMT-" + star_id


@string_name
def koi(star_id):
    if len(star_id) > 1:
        return "KOI-" + str('%04i' % star_id[0]) + star_id[1]
    else:
        return "KOI-" + str('%04i' % star_id[0])

@string_name
def lamost(star_id):
    if star_id[0].lower() == "j":
        return "LAMOST " + star_id.upper()
    else:
        return "LAMOST J" + star_id

@string_name
def lhs(star_id):
    if len(star_id) > 1:
        return "LHS " + str('%04i' % star_id[0]) + star_id[1]
    else:
        return "LHS " + str('%04i' % star_id[0])


@string_name
def l(star_id):
    if len(star_id) < 3:
        return "L " + str(star_id[0]) + "-" + str(star_id[1])
    else:
        return "L " + str(star_id[0]) + "-" + str(star_id[1]) + star_id[2]


@string_name
def lp(star_id):
    if len(star_id) < 3:
        return "LP " + str("%03i" % star_id[0]) + "-" + str("%02i" % star_id[1])
    else:
        return "LP " + str("%03i" % star_id[0]) + "-" + str("%02i" % star_id[1]) + star_id[2]


@string_name
def lspm(star_id):
    return "LSPM " + star_id.upper()


@string_name
def ltt(star_id):
    if len(star_id) < 2:
        return "LTT " + str("%05i" % star_id[0])
    else:
        return "LTT " + str("%05i" % star_id[0]) + star_id[1]


@string_name
def lupus(star_id):
    return "Lupus" + star_id[0].upper() + " " + str(star_id[1])


@string_name
def m(star_id):
    return "M " + star_id


@string_name
def mascara(star_id):
    if len(star_id) < 2:
        return "MASCARA-" + str(star_id[0])
    else:
        return "MASCARA-" + str(star_id[0]) + star_id[1]


@string_name
def moa(star_id):
    return "MOA" + star_id


@string_name
def mxb(star_id):
    return "MXB " + star_id


@string_name
def name(star_id):
    return "NAME " + star_id


@string_name
# Two kinds of NGC star names
def ngc(star_id):
    if len(star_id) < 12:
        return "NGC " + star_id
    else:
        return "Cl* NGC " + star_id


@string_name
def ngts(star_id):
    if len(star_id) > 1:
        return "NGTS-" + str(star_id[0]) + star_id[1]
    else:
        return "NGTS-" + str(star_id[0])

@string_name
def nltt(star_id):
    if len(star_id) < 2:
        return "NLTT " + str("%05i" % star_id[0])
    elif type(star_id) == str:
        return "NLTT " + star_id
    else:
        return "NLTT " + str("%05i" % star_id[0]) + star_id[1]

@string_name
def nsvs(star_id):
    if len(star_id) > 1:
        return "NSVS " + str(star_id[0]) + star_id[1]
    else:
        return "NSVS " + str(star_id[0])


@string_name
def ogle(star_id):
    return "OGLE-" + star_id


@string_name
def ogletr(star_id):
    return "OGLE-TR " + str(star_id[0])


@string_name
def pds(star_id):
    if len(star_id) > 1:
        return "PDS " + str(star_id[0]) + star_id[1]
    else:
        return "PDS " + str(star_id[0])


@string_name
def ph(star_id):
    if len(star_id) > 1:
        return "PH " + str(star_id[0]) + star_id[1]
    else:
        return "PH " + str(star_id[0])


@string_name
def pots(star_id):
    if len(star_id) > 1:
        return "POTS-" + str(star_id[0]) + star_id[1]
    else:
        return "POTS-" + str(star_id[0])


@string_name
def psr(star_id):
    return "PSR " + star_id


@string_name
def qatar(star_id):
    if len(star_id) > 1:
        return "Qatar " + str(star_id[0]) + star_id[1]
    else:
        return "Qatar " + str(star_id[0])

@string_name
def rave(star_id):
    if star_id[0].lower() == "j":
        return "RAVE " + star_id.upper()
    else:
        return "RAVE J" + star_id

@string_name
def ross(star_id):
    if len(star_id) > 1:
        return "Ross " + str('%04i' % star_id[0]) + star_id[0]
    else:
        return "Ross " + str('%04i' % star_id[0])


@string_name
def roxs(star_id):
    if len(star_id) > 1:
        return "ROXs " + str('%04i' % star_id[0]) + star_id[1]
    else:
        return "ROXs " + str('%04i' % star_id[0])


@string_name
def rx(star_id):
    return "RX " + star_id


@string_name
def sun(star_id):
    return None


@string_name
def sweeps(star_id):
    if len(star_id) > 1:
        return "SWEEPS " + str(star_id[0]) + star_id[1]
    else:
        return "SWEEPS " + str(star_id[0])


@string_name
def tap(star_id):
    if len(star_id) > 1:
        return "TAP " + str(star_id[0]) + star_id[1]
    else:
        return "TAP " + str(star_id[0])

@string_name
def tic(star_id):
    if len(star_id) > 1:
        return "TIC " + str(star_id[0]) + star_id[1]
    else:
        return "TIC " + str(star_id[0])

@string_name
def toi(star_id):
    if len(star_id) > 1:
        return "TOI " + str(star_id[0]) + star_id[1]
    else:
        return "TOI " + str(star_id[0])


@string_name
def tcp(star_id):
    return "TCP " + star_id.upper()


@string_name
def trappist(star_id):
    if len(star_id) > 1:
        return "TRAPPIST-" + str(star_id[0]) + star_id[1]
    else:
        return "TRAPPIST- " + str(star_id[0])


@string_name
def tres(star_id):
    if len(star_id) > 1:
        return "TrES-" + str(int(star_id[0])) + star_id[1]
    else:
        return "TrES-" + str(int(star_id[0]))


@string_name
def tyc(star_id):
    return "TYC " + str("%04i" % star_id[0]) + "-" + str("%05i" % star_id[1]) + "-" + str(star_id[2])


@string_name
def two_mass(star_id):
    if star_id[0].lower() == "j":
        return "2MASS " + star_id.upper()
    else:
        return "2MASS J" + star_id


@string_name
def two_massi(star_id):
    if star_id[0].lower() == "j":
        return "2MASSI " + star_id.upper()
    else:
        return "2MASSI J" + star_id


@string_name
def uscoctio(star_id):
    if len(star_id) > 1:
        return "UScoCTIO " + str(star_id[0]) + star_id[1]
    else:
        return "UScoCTIO " + str(star_id[0])


@string_name
def ukirt(star_id):
    return "UKIRT-" + star_id.upper()


@string_name
def v_asterisk(star_id):
    return "V* " + star_id.upper()


@string_name
def vhs(star_id):
    return "VHS " + star_id.upper()


@string_name
def wasp(star_id):
    if len(star_id) > 1:
        return "WASP-" + str('%03i' % int(star_id[0])) + star_id[1]
    else:
        return "WASP-" + str('%03i' % int(star_id[0]))


@string_name
def wd(star_id):
    if len(star_id) > 2:
        return "WD " + str(star_id[0]) + "-" + str(star_id[1]) + star_id[2]
    else:
        return "WD " + str(star_id[0]) + "-" + str(star_id[1])


@string_name
def wds(star_id):
    return "WDS " + star_id

@string_name
def wendelstein(star_id):
    if len(star_id) > 1:
        return "Wendelstein-" + str(star_id[0]) + star_id[1]
    else:
        return "Wendelstein- " + str(star_id[0])


@string_name
def wise(star_id):
    return "WISE " + star_id


@string_name
def wolf(star_id):
    if len(star_id) > 1:
        return "Wolf " + str(int(star_id[0])) + star_id[1]
    else:
        return "Wolf " + str(int(star_id[0]))


@string_name
def wts(star_id):
    if len(star_id) > 1:
        return "WTS-" + str(int(star_id[0])) + star_id[1]
    else:
        return "WTS-" + str(int(star_id[0]))


@string_name
def xo(star_id):
    return "XO" + star_id

@string_name
def yses(star_id):
    if len(star_id) < 2:
        return "YSES " + str("%05i" % star_id[0])
    else:
        return "YSES " + str("%05i" % star_id[0]) + star_id[1]


rename_dict = {"2mass": 'two_mass',
               "2massi": 'two_massi',
               "ogle-tr": "ogletr",
               "*": "asterisk",
               "v*": "v_asterisk",
               "**": "double_asterisk",
               "em*": "em_asterisk",
               "cl*_ngc": 'cl_ngc',
               "cfhtwir-oph": "cfhtwir_oph"}
rename_set = set(rename_dict.keys())


class StringStarName:
    def __init__(self, hypatia_name: tuple):
        self.hypatia_name = hypatia_name
        self.name_type = self.hypatia_name[0]
        if " " in self.name_type:
            self.name_type = self.name_type.replace(" ", "_")
        if self.name_type in rename_set:
            self.name_type = rename_dict[self.name_type]
        self.name_id = self.hypatia_name[1]
        self.string_name = format_functions[self.name_type](self.name_id)

    def __call__(self) -> str:
        return self.string_name


def calc_simbad_name(input_name: str, key: str = None) -> str:
    hypatia_name = star_name_format(input_name, key=key)
    return StringStarName(hypatia_name)()


if __name__ == "__main__":
    test = star_name_format("2MASSI J0840424+193357")
    test2 = star_name_format("2MASS 16361119+4636479")