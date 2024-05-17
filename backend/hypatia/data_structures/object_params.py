from collections import UserDict
from typing import NamedTuple, Union, Optional


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
            self.data[str(param_name)] = set_single_param(new_param_dict)


class SingleParam(NamedTuple):
    """ Represents all the attributes for a single parameter value."""
    value: Union[float, int, str]
    err_low: Optional[Union[float, int, str, tuple]] = None
    err_high: Optional[Union[float, int, str, tuple]] = None
    ref: Optional[str] = None
    units: Optional[str] = None


def set_single_param(param_dict=None, value=None, err_low=None, err_high=None, units=None, ref=None):
    if param_dict is not None:
        keys = set(param_dict.keys())
        if "value" in keys:
            internal_param_dict = {}
            for param_key in SingleParam._fields:
                if param_key in keys:
                    internal_param_dict[param_key] = param_dict[param_key]
                else:
                    internal_param_dict[param_key] = None
            return SingleParam(value=internal_param_dict["value"],
                               err_low=internal_param_dict['err_low'],
                               err_high=internal_param_dict['err_high'],
                               units=internal_param_dict['units'],
                               ref=internal_param_dict['ref'])
    elif value is not None:
        return SingleParam(value=value, err_low=err_low, err_high=err_high, units=units, ref=ref)
    raise ValueError("A key named 'value' is needed to set a parameter")

