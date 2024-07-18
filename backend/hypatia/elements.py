import os
import tomllib
from typing import NamedTuple

from hypatia.config import ref_dir, site_dir
from hypatia.tools.table_read import row_dict


plusminus_error_default = 0.001
elements_that_end_in_h = {'bh', 'rh', 'th', 'nh', 'h'}
ambiguous_ion_elements = {frozenset({'s', 'si'}), frozenset({'n', 'ni'}), frozenset({'b', 'bi'})}
elements_that_end_in_i = {'li', 'si', 'ti', 'ni', 'bi', 'i'}
single_letter_elements_with_same_first_letter = {'s', 'n', 'b', 'i'}

expected_ion_states_upper = ["IV", "III", 'II']
expected_ion_states = [state.lower() for state in expected_ion_states_upper]

float_params = {"ionization_energy_ev", 'average_mass_amu'}
elements_found = set()
# from the chemical data CSV file
element_csv = {key: {field_name: float(value) if field_name in float_params else value
                     for field_name, value in el_dict.items()}
               for key, el_dict in row_dict(os.path.join(ref_dir, "elementData.csv"), key='element_abrev').items()}

# representative error file
element_plusminus_error_file = os.path.join(site_dir, 'element_plusminus_err.toml')
with open(element_plusminus_error_file, 'rb') as f:
    plusminus_error = {key.lower(): float(value) for key, value in tomllib.load(f).items()}


summary_dict = {}
for el_name, el_dict in element_csv.items():
    el_name_lower = el_name.lower()
    # make a shallow copy of the element dictionary as a part of this data export
    el_data = {**el_dict, "abbreviation": el_name, "plusminus": plusminus_error.get(el_name_lower, plusminus_error_default)}
    summary_dict[el_name_lower] = el_data


def under_score_clean_up(a_string: str) -> str:
    while "__" in a_string:
        a_string = a_string.replace("__", "_")
    return a_string.strip('_')


def is_one_uppercase(string: str) -> bool:
    for char in string:
        if char.isupper():
            return True
    return False


def ion_state_by_underscore(user_element_lower: str) -> str | None:
    if "_" in user_element_lower:
        for possible_ion_state in user_element_lower.split("_"):
            if possible_ion_state in expected_ion_states:
                return possible_ion_state
    return None


def format_found_ion_state(user_element: str, user_element_lower: str, ion_state: str) -> tuple[str, str]:
    start_index = user_element_lower.find(ion_state)
    return under_score_clean_up(user_element[:start_index] + user_element[start_index + len(ion_state):]), ion_state


def find_possible_ion_states(user_element_lower: str) -> set[str]:
    possible_ion_states = set()
    for possible_ion_state in expected_ion_states:
        if user_element_lower.endswith(possible_ion_state):
            possible_ion_states.add(possible_ion_state)
    return possible_ion_states


def ion_state_unambiguous_case_insensitive(user_element_lower: str) -> str | None:
    """It is expected that this is an ion state to detect, but this only will return the ion state if found."""
    possible_element_names = set()
    for element_name in summary_dict.keys():
        if user_element_lower.startswith(element_name):
            possible_element_names.add(element_name)
    possible_element_names_len = len(possible_element_names)
    if possible_element_names_len == 0:
        raise ValueError(f"Element {user_element_lower} not found in the element dictionary.")
    if possible_element_names_len > 2:
        raise ValueError(f"Element {user_element_lower} has too many match, found {len(possible_element_names)} possible matches.")
    if possible_element_names_len == 2:
        if frozenset(possible_element_names) in ambiguous_ion_elements:
            possible_ion_states = find_possible_ion_states(user_element_lower)
            if any([a_state.startswith('i') for a_state in possible_ion_states]):
                # this is an ambiguous case, so we will not return a value
                return None
        # use the longer element name
        element_name = max(possible_element_names, key=len)
    else:
        element_name = possible_element_names.pop()
    ion_state_sub_string = user_element_lower[len(element_name):]
    possible_ion_states = find_possible_ion_states(ion_state_sub_string)
    # use the only ion state found
    if len(possible_ion_states) == 1:
        return possible_ion_states.pop()
    # this is an ambiguous case, so we will not return a value
    return None


def ion_state_parse(user_element: str) -> tuple[str, str | None]:
    """
    Parse the ion state from the user input string, there are a lot of special cases, so use this function as a
    last try to parse the ion state from the user input string.
    """
    if len(user_element) < 2:
        # ionization states require at least two or more characters
        return user_element, None
    user_element_lower = user_element.lower()
    found_ion_state = ion_state_by_underscore(user_element_lower)
    if found_ion_state is not None:
        return format_found_ion_state(user_element, user_element_lower, found_ion_state)
    # can it be parsed ignoring case?
    found_ion_state = ion_state_unambiguous_case_insensitive(user_element_lower)
    if found_ion_state is not None:
        return format_found_ion_state(user_element, user_element_lower, found_ion_state)
    # since there are no underscores in the user input string, we will try to find the ion state by the last uppercase
    if user_element[-1].isupper():
        # this is not a single letter element, so ending in an uppercase letter is a strong indicator of an ion state
        for possible_ion_state_upper in expected_ion_states_upper:
            if user_element.endswith(possible_ion_state_upper):
                return format_found_ion_state(user_element, user_element_lower, possible_ion_state_upper.lower())
    # This ion state was not a parsable or did not exist.
    return user_element, None


class ElementID(NamedTuple):
    name_lower: str
    ion_state: str | None
    is_nlte: bool

    def __str__(self):
        return_s = ""
        if self.is_nlte:
            return_s += "NLTE_"
        return_s += summary_dict[self.name_lower]['abbreviation']
        if self.ion_state is not None:
            return_s += f"_{self.ion_state.upper()}"
        return return_s

    @classmethod
    def from_str(cls, element_string: str):
        element_string = element_string.strip().replace(" ", "_")
        element_string_lower = element_string.lower()
        if len(element_string) == 0:
            raise ValueError("Element string is empty, no element data can be returned.")
        elif len(element_string) == 1:
            if element_string_lower in summary_dict.keys():
                return cls(summary_dict[element_string_lower]['abbreviation'].lower(), None, False)
            else:
                raise KeyError(f"Element {element_string} not found in the element dictionary.")
        # the element string is at least two characters long
        is_nlte = element_string_lower.startswith("nlte")
        if is_nlte:
            element_string_lower = element_string_lower[4:].strip("_")
            element_string = element_string[4:].strip("_")
        # strip out the uppercase ionization state numerals
        for numeral_str in expected_ion_states:
            if element_string_lower.endswith(numeral_str):
                # this triggers a special case detection system
                element_string, ion_state = ion_state_parse(element_string)
                element_string_lower = element_string.lower()
                break
        else:
            ion_state = None
        # strip out a possible hydrogen suffix
        if element_string_lower[-1] == "h" and element_string_lower not in elements_that_end_in_h:
            element_string_lower = element_string_lower[:-1].strip('_')
        if element_string_lower in summary_dict.keys():
            name_lower = summary_dict[element_string_lower]['abbreviation'].lower()
        else:
            raise KeyError(f"Element {element_string} not found in the element dictionary.")
        new_record = cls(name_lower=name_lower, ion_state=ion_state, is_nlte=is_nlte)
        # track the unique elements that are in the pipeline
        elements_found.add(new_record)
        return new_record

    def __repr__(self):
        return f"ElementID({self})"


class RatioID(NamedTuple):
    numerator: ElementID
    denominator: ElementID

    def __str__(self):
        return f"[{self.numerator}/{self.denominator}]"

    @classmethod
    def from_str(cls, ratio_string: str = None, numerator_element: str = None, denominator_element: str = None):
        if ratio_string is not None:
            ratio_string = ratio_string.replace("[", "").replace("]", "")
            ratio_elements = ratio_string.split("/")
            if len(ratio_elements) != 2:
                raise ValueError(f"Ratio string {ratio_string} does not have two elements.")
            numerator_element = ratio_elements[0]
            denominator_element = ratio_elements[1]
        elif numerator_element is None:
            raise ValueError("No ratio string or numerator element string provided.")
        elif denominator_element is None:
            denominator_element = "H"
        return cls(numerator=ElementID.from_str(numerator_element), denominator=ElementID.from_str(denominator_element))

    def __repr__(self):
        return f"RatioID({self})"


def element_rank(element_record: ElementID) -> float:
    """Use this key in a sorting list like : sorted(list[ElementRecord], key=element_rank)"""
    name_lower = element_record.name_lower
    ion_state = element_record.ion_state
    rank = float(summary_dict[name_lower]["atomic_number"])
    if element_record.is_nlte:
        rank += 0.001
    if ion_state is not None:
        ion_state = ion_state.lower()
        if ion_state == "i":
            rank += 0.0001
        elif ion_state == "ii":
            rank += 0.00011
        elif ion_state == "iii":
            rank += 0.000111
    return rank


def get_representative_error(element_id: ElementID) -> float:
    return plusminus_error.get(element_id.name_lower, plusminus_error_default)


hydrogen_id = ElementID.from_str("H")
iron_id = ElementID.from_str("Fe")
iron_ii_id = ElementID.from_str("Fe_II")
iron_nlte_id = ElementID.from_str("NLTE_Fe")
