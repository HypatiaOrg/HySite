import os
import tomllib
from typing import NamedTuple

from hypatia.config import ref_dir, site_dir
from hypatia.tools.table_read import row_dict


plusminus_error_default = 0.001
elements_that_end_in_h = {'bh', 'rh', 'th', 'h'}
# elements_that_end_in_i = {'li', 'si', 'ti', 'ni', 'bi'}
expected_ion_states = ["IV", "III", 'II']
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


def under_score_clean_up(a_string: str) -> str:
    while "__" in a_string:
        a_string = a_string.replace("__", "_")
    return a_string


summary_dict = {}
for el_name, el_dict in element_csv.items():
    el_name_lower = el_name.lower()
    # make a shallow copy of the element dictionary as a part of this data export
    el_data = {**el_dict, "abbreviation": el_name, "plusminus": plusminus_error.get(el_name_lower, plusminus_error_default)}
    summary_dict[el_name_lower] = el_data


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
            if numeral_str in element_string:
                ion_state = numeral_str.lower()
                element_string = element_string.replace(numeral_str, '')
                element_string_lower = element_string.lower().strip('_')
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
