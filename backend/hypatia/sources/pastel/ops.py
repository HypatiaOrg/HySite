from time import time

from hypatia.sources.pastel.db import PastelCollection
from hypatia.object_params import ObjectParams, SingleParam
from hypatia.sources.pastel.read import load_from_file, param_to_unit


def upload_pastel_data(verbose: bool = True) -> None:
    pastel_data, simbad_id_to_pastel_ids = load_from_file(verbose=verbose)
    mongo_format = []
    for main_id, object_params in pastel_data.items():
        mongo_format.append({
            '_id': main_id,
            'pastel_ids': list(simbad_id_to_pastel_ids[main_id]),
            'timestamp': time(),
            'data': {param_name: [single_param.to_record(param_str=param_name) for single_param in list(param_set)] for
                     param_name, param_set in object_params.data.items()}
        })
    pastel_collection = PastelCollection(db_name='metadata', collection_name='pastel')
    pastel_collection.reset()
    pastel_collection.add_many(mongo_format)


def get_pastel_data(verbose: bool = True) -> dict[str, ObjectParams]:
    if verbose:
        print('    Loading Pastel data from MongoDB database...')
    pastel_collection = PastelCollection(db_name='metadata', collection_name='pastel')
    if verbose:
        print('    Data fetched, formatting...')
    pastel_data = {}
    for doc in pastel_collection.find_all():
        main_id = doc['_id']
        object_params = ObjectParams()
        params_this_star = doc['data']
        for param_name, param_set in params_this_star.items():
            for param in param_set:
                object_params[param_name] = SingleParam.strict_format(param_name=param_name, value=param['value'],
                                                                      ref=param['ref'], units=param_to_unit[param_name])
        pastel_data[main_id] = object_params
    if verbose:
        print('    Pastel data loaded')
    return pastel_data


if __name__ == '__main__':
    # Upload data from the Pastel file to the database
    upload_pastel_data(verbose=True)
    # Get the Pastel data from the database
    pastel_data = get_pastel_data()