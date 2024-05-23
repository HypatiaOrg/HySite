import os
import tomllib

from hypatia.config import ref_dir, site_dir
from hypatia.tools.table_read import row_dict

# chemical data CSV
float_params = {"ionization_energy_ev", 'average_mass_amu'}
element_dict = {key: {field_name: float(value) if field_name in float_params else value
                      for field_name, value in el_dict.items()}
                for key, el_dict in row_dict(os.path.join(ref_dir, "elementData.csv"), key='element_abrev').items()}
all_elements = set(element_dict.keys())

# representative error file
element_plusminus_error_file = os.path.join(site_dir, 'element_plusminus_err.toml')
with open(element_plusminus_error_file, 'rb') as f:
    plusminus_error = {key.lower(): float(value) for key, value in tomllib.load(f).items()}


def check_number(tail):
    number_string = ""
    letter_string = ""
    for letter in tail:
        try:
            _ = float(letter)
        except ValueError:
            letter_string += letter
        else:
            number_string += letter
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


def get_representative_error(element_name: str) -> float:
    return plusminus_error.get(element_name.lower(), 0.001)


def website_chemical_summary():
    summary_dict = {}
    for el_name, el_dict in element_dict.items():
        el_name_lower = el_name.lower()
        # make a shallow copy of the element dictionary as a part of this data export
        el_data = {**el_dict, "abbreviation": el_name, "plusminus": get_representative_error(el_name)}
        summary_dict[el_name_lower] = el_data
    return summary_dict


class ElementParse:
    def __init__(self):
        self.summary_dict = website_chemical_summary()

    def web_name_parse(self, element_string) -> tuple[str, int | None, bool]:
        ionization_state_numeral = None
        hydrogen_suffix = False
        element_string_lower = element_string.lower()
        if len(element_string_lower) < 1:
            raise ValueError("Element string is empty, no element data can be returned.")
        test_packages = []
        if len(element_string_lower) > 1:
            # test of two letter element names
            test_packages.append((element_string_lower[:2], element_string[2:]))
        # test of 1 letter element names
        test_packages.append((element_string_lower[0], element_string[1:]))
        for head, tail in test_packages:
            if head in self.summary_dict.keys():
                el_data = self.summary_dict[head]
                el_name = el_data["abbreviation"]
                break
        else:
            raise KeyError(f"Element {element_string} not found in the element dictionary.")
        if tail:
            if tail[0] == 'h':
                hydrogen_suffix = True
                tail = tail[1:]
            if tail:
                ionization_state_numeral = 0
                for letter in tail:
                    if letter == 'I':
                        ionization_state_numeral += 1
                    else:
                        raise ValueError(f"Unexpected character {letter} in ionization state numeral for element str {element_string}.")
        return el_name, ionization_state_numeral, hydrogen_suffix


elements_that_end_in_i = {'li', 'si', 'ti', 'ni', 'bi'}
start_letters_for_elements_that_end_in_i = {el[0] for el in elements_that_end_in_i}
if __name__ == "__main__":
    el_parse = ElementParse()
    el_name, ionization, hydrogen_suffix = el_parse.web_name_parse('feii')
    for key, value in el_parse.summary_dict.items():
        if key[-1] == 'i':
            print(key, "I Issue")
        elif key in start_letters_for_elements_that_end_in_i:
            print(key, "Start letter Issue")