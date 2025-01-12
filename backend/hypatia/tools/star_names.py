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

# for nat_cat.py
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


if __name__ == "__main__":
    test = star_name_format("2MASSI J0840424+193357")
    test2 = star_name_format("2MASS 16361119+4636479")