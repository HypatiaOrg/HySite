import os
from hypatia.config import ref_dir
from hypatia.load.table_read import row_dict

element_dict = row_dict(os.path.join(ref_dir, "elementData.csv"), key='element_abrev')
all_elements = set(element_dict.keys())


def check_number(tail):
    number_string = ""
    letter_string = ""
    for letter in tail:
        try:
            _ = float(letter)
            number_string += letter
        except:
            letter_string += letter
    if number_string == "":
        number_string = None
    if letter_string == "":
        number_string = None
    return number_string, letter_string


def element_parse(element_string):
    abrev = None
    isotope = None
    ionization = None
    if len(element_string) == 1:
        # Case the of element _string = H, C, or O
        abrev = element_string
    elif len(element_string) > 1:
        if element_string[1].islower():
            abrev = element_string[0:2]
            if len(element_string) > 2:
                number_string, letter_string = check_number(element_string[2:])
                if number_string is not None:
                    isotope = int(number_string)
                if letter_string is not None:
                    ionization = letter_string
        else:
            abrev = element_string[0]
            number_string, letter_string = check_number(element_string[1:])
            if number_string is not None:
                isotope = int(number_string)
            if letter_string is not None:
                ionization = letter_string
    return abrev, isotope, ionization


# Send in a list that looks like: sorted([list_of_elements], key=element_rank)
def element_rank(element_string):
    abrev, isotope, ionization = element_parse(element_string)
    rank = float(element_dict[abrev]["atomic_number"])
    if isotope is not None:
        rank += float(isotope) / 1000.0
    if ionization is not None:
        if ionization.lower() == "i":
            rank += 0.0001
        elif ionization.lower() == "ii":
            rank += 0.00011
        elif ionization.lower() == "iii":
            rank += 0.000111
        elif ionization.lower() == "iv":
            rank += 0.0001111
        elif ionization.lower() == "v":
            rank += 0.00011111
        elif ionization.lower() == "vi":
            rank += 0.000111111
    return rank
