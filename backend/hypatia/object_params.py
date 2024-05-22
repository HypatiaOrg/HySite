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


class SingleParam(NamedTuple):
    """ Represents all the attributes for a single parameter value."""
    value: Union[float, int, str]
    err_low: Optional[Union[float, int, str, tuple]] = None
    err_high: Optional[Union[float, int, str, tuple]] = None
    ref: Optional[str] = None
    units: Optional[str] = None

    def to_record(self, param_str: str):
        value = self.value
        ref = self.ref
        err_low = self.err_low
        err_high = self.err_high
        units = self.units
        if param_str not in expected_params:
            raise ValueError(f"Parameter {param_str}, ref:{ref} is not in the expected parameters list")
        # do type checking for the input to Match the expected Database fields and the units
        expected_units = expected_params_dict[param_str].get('units', None)
        if expected_units == 'string':
            return {key: self.__getattribute__(key) for key in ['value', 'ref']
                    if self.__getattribute__(key) is not None}
        elif expected_units == "":
            pass
        elif expected_units != units:
            raise ValueError(f"Expected units for {param_str}, ref:{ref} are {expected_units}, not {self.units}")
        if isinstance(value, int):
            if isinstance(err_low, float) or isinstance(err_high, float):
                value = float(value)
                if err_low is not None:
                    err_low = float(err_low)
                if err_high is not None:
                    err_high = float(self.err_high)
        if isinstance(value, float):
            if err_low is not None:
                err_low = float(err_low)
            if err_high is not None:
                err_high = float(err_high)
            if err_low is not None and err_high is not None:
                value, err_low, err_high = format_by_err(value, err_low, err_high)
        return {key: attr_val for key, attr_val
                in [('value', value), ('ref', ref), ('err_low', err_low), ('err_high', err_high)]
                if attr_val is not None}
