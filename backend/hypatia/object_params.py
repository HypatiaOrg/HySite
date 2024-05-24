import os
import tomllib
from collections import UserDict
from typing import NamedTuple, Union, Optional

import numpy as np

from hypatia.config import site_dir


params_and_units_file = os.path.join(site_dir, 'params_units.toml')


def get_params_and_units_from_file() -> dict:
    with open(params_and_units_file, 'rb') as f:
        return tomllib.load(f)


expected_params_dict = get_params_and_units_from_file()
expected_params = set(expected_params_dict.keys())


def params_value_format(value, decimals):
    try:
        formatted_value = float(np.round(value, decimals=decimals))
    except TypeError:
        formatted_value = value
    return formatted_value


def params_err_format_string(err: float, sig_figs: int) -> str:
    if sig_figs < 2:
        minors = 1
    else:
        minors = sig_figs - 1
    format_string = f'1.{minors}e'
    return err.__format__(format_string)


def params_err_format(err: float, sig_figs: int) -> float:
    return float(params_err_format_string(err, sig_figs))


def format_by_err(value: float, err_low: float, err_high: float, sig_figs: int = 3):
    err_low_str = params_err_format_string(err_low, sig_figs)
    err_low_exp = int(err_low_str.split('e')[1])
    err_high_str = params_err_format_string(err_high, sig_figs)
    err_high_exp = int(err_high_str.split('e')[1])
    decimals = sig_figs - min(err_low_exp, err_high_exp) - 1
    value = np.around(value, decimals=decimals)
    err_low = np.around(err_low, decimals=decimals)
    err_high = np.around(err_high, decimals=decimals)
    return value, err_low, err_high


class StarDict(UserDict):
    def __missing__(self, key):
        if isinstance(key, str):
            raise KeyError
        return self[str(key)]

    def __contains__(self, key):
        return str(key) in self.data

    def __setitem__(self, key, value):
        if not self.__contains__(key):
            if isinstance(value, set):
                self.data[str(key)] = value
            else:
                self.data[str(key)] = {value}
        if isinstance(value, set):
            self.data[str(key)] |= value
        else:
            self.data[str(key)].add(value)


class ObjectParams(StarDict):
    def __setitem__(self, key, value):
        key = key.lower()
        if self.__contains__(key):
            if isinstance(value, set):
                self.data[str(key)] |= value
            elif isinstance(value, SingleParam):
                self.data[str(key)].add(value)
            else:
                raise ValueError("SingleParam or set is required")
        else:
            if isinstance(value, set):
                self.data[str(key)] = value
            elif isinstance(value, SingleParam):
                self.data[str(key)] = {value}
            else:
                raise ValueError("SingleParam or set is required")

    def update_single_ref_source(self, ref_str, params_dict):
        new_param_dict = {}
        for param_name in params_dict.keys():
            new_param_dict["value"] = params_dict[param_name]
            new_param_dict['ref'] = ref_str
            self.data[str(param_name)] = SingleParam(**new_param_dict)


values_types = int | float | str


def single_param_strict_check(param_name: str, value: values_types, ref: str, units: str,
                              err_low: values_types = None, err_high: values_types = None) -> dict[str, values_types]:
    param_name = str(param_name).lower().strip()
    if param_name not in expected_params:
        raise ValueError(f"Strict Checking: Parameter {param_name}, ref:{ref} is not in the expected parameters list")
    if value is None:
        raise ValueError(f"Strict Checking: Value for {param_name}, ref:{ref} is None")
    if ref is None:
        raise ValueError(f"Strict Checking: Reference for {param_name}, value:{value} is None")
    if units is None:
        raise ValueError(f"Strict Checking: Units for {param_name}, value:{value}, ref:{ref} is None, " +
                         "but it can be set as an empty string in the reference file.")
    # do type checking for the input to Match the expected Database fields and the units
    expected_values_this_param = expected_params_dict.get(param_name, None)
    if expected_values_this_param is None:
        raise KeyError(f"Strict Checking: No entry for {param_name}, ref:{ref} are not found in the reference file")
    expected_units = expected_params_dict[param_name].get('units', None)
    if expected_units is None:
        raise KeyError(f"Strict Checking: Expected units for {param_name}, is not found the reference file")
    if expected_units == 'string':
        return {'value': value, 'ref': ref, 'units': 'string'}
    elif expected_units == "":
        # unless parameters like Log(G) can be ignored in this check
        pass
    elif expected_units != units:
        raise ValueError(f"Expected units for {param_name}, ref:{ref} are {expected_units}, not {units}")
    if isinstance(value, int):
        if isinstance(err_low, float) or isinstance(err_high, float):
            value = float(value)
            if err_low is not None:
                err_low = float(err_low)
            if err_high is not None:
                err_high = float(err_high)
    if isinstance(value, float):
        if err_low is not None:
            err_low = float(err_low)
        if err_high is not None:
            err_high = float(err_high)
        if err_low is not None and err_high is not None:
            value, err_low, err_high = format_by_err(value, err_low, err_high)
    if err_low is None or err_high is None:
        # when there are no error values, we can round bases on the expected number of decimals
        # if that is provided in the reference file
        decimals_for_rounding = expected_params_dict[param_name].get('decimals', None)
        if decimals_for_rounding is not None:
            value = params_value_format(value, decimals_for_rounding)
        return {'value': value, 'ref': ref, 'units': units}
    return {'value': value, 'ref': ref, 'units': units, 'err_low': err_low, 'err_high': err_high}


class SingleParam(NamedTuple):
    """ Represents all the attributes for a single parameter value."""
    value: values_types
    ref: str
    units: str
    err_low: values_types = None
    err_high: values_types = None

    @classmethod
    def strict_format(cls, param_name: str, value: values_types, ref: str, units: str,
                      err_low: values_types = None, err_high: values_types = None):
        return cls(**single_param_strict_check(param_name, value, ref, units, err_low, err_high))

    def to_record(self, param_str: str):
        value = self.value
        ref = self.ref
        err_low = self.err_low
        err_high = self.err_high
        units = self.units
        rec = single_param_strict_check(param_str, value, ref, units, err_low, err_high)
        if "units" in rec.keys():
            del rec["units"]
        return rec

