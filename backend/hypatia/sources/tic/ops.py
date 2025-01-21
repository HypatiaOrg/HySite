import numpy as np

from hypatia.sources.tic.query import query_tic_data
from hypatia.sources.simbad.ops import get_star_data
from hypatia.object_params import ObjectParams, SingleParam
from hypatia.sources.tic.db import TICStarCollection, primary_values


tic_reference = "TESS Input Catalog"
error_to_primary_values = {f"{primary_value}_err": primary_value for primary_value in primary_values}
primary_values_to_error = {primary_value: f"{primary_value}_err" for primary_value in primary_values}
error_field_conversion = {f"e_{primary_value}": f"{primary_value}_err" for primary_value in primary_values}
tic_data_wanted = primary_values | error_field_conversion.keys()
units_dict = {"Teff": "K", "logg": "cgs", "mass": "M_sun", "rad": "R_sun"}
params_with_units = set(units_dict.keys())
name_preference = ["gaia dr2", "2mass", "tyc", "hip"]
allowed_names = {name_type for name_type in name_preference}

tic_collection = TICStarCollection(collection_name="tic", name_col="_id")
tic_cache = {tic_doc['_id']: tic_doc for tic_doc in tic_collection.find_all()}


def get_tic_data(star_name: str) -> dict or None:
    simbad_doc = get_star_data(star_name, test_origin="tic")
    main_star_id = simbad_doc["_id"]
    if main_star_id in tic_cache.keys():
        return tic_cache[main_star_id]
    tic_doc = tic_collection.find_by_id(main_star_id)
    if tic_doc:
        if tic_doc['is_tic']:
            return tic_doc
        else:
            # The star is not in the TIC sources queried before
            return None
    """ The Data was not found in the local sources, can we find it in the TIC sources?"""
    # get the allowed star names from the TIC sources
    for name_type in name_preference:
        if name_type in simbad_doc.keys():
            allowed_star_name = simbad_doc[name_type]
            break
    else:
        # None of the star's names can be used to query the TIC sources, we cannot proceed
        return None
    tic_dict = query_tic_data(allowed_star_name)
    if tic_dict is None:
        # The query failed to return any data
        tic_collection.set_null_record(main_star_id)
        print(f"  No TIC data found for main_star_id: {main_star_id}")
        return None
    # parse the TIC data and add it to the local sources.
    found_params = set(tic_dict.keys()) & tic_data_wanted
    data_params = {field_name: float(tic_dict[field_name][0]) for field_name in found_params}
    for key, value in list(data_params.items()):
        if key.startswith('e_'):
            new_error_field = error_field_conversion[key]
            data_params[new_error_field] = value
            del data_params[key]
    # restructure the data to match the local pattern
    data_record = {}
    for primary_field in primary_values:
        if primary_field in data_params.keys():
            primary_value = data_params[primary_field]
            error_field = primary_values_to_error[primary_field]
            params_data = {}
            if not np.isnan(primary_value):
                params_data['value'] = primary_value
                if error_field in data_params.keys():
                    error_value = data_params[error_field]
                    if not np.isnan(error_value):
                        params_data['err'] = error_value

            if params_data:
                data_record[primary_field] = params_data
    # add the units to the data record
    tic_collection.set_record(main_star_id, data_record)
    tic_cache[main_star_id] = tic_collection.find_by_id(main_star_id)
    print(f"  TIC data added to the hypatia sources for main_star_id: {main_star_id}")
    # try again to get the newly updated star data from the local sources
    return get_tic_data(star_name=star_name)


def get_hy_tic_data(star_name: str) -> dict or None:
    tic_doc = get_tic_data(star_name)
    if tic_doc is None:
        return None
    tic_data = tic_doc.get('data', {})
    if tic_doc['is_tic'] and tic_data:
        object_params = ObjectParams()
        for field_name in tic_data.keys():
            field_data = tic_data[field_name]
            if 'value' in field_data:
                field_data['units'] = units_dict[field_name]
            field_data['ref'] = tic_reference
            if 'err' in field_data:
                field_data['err_low'] = field_data['err']
                field_data['err_high'] = field_data['err']
                del field_data['err']
            object_params[field_name] = SingleParam.strict_format(param_name=field_name, **field_data)
        return object_params
    return None


if __name__ == "__main__":
    # tic_collection.reset()
    tic_doc = get_tic_data("TYC 4767-00765-1")
