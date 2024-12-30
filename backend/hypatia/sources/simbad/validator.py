single_star_param_double = {
    'bsonType': 'object',
    'description': 'The curated data object for a single-star stellar-parameter',
    'required': ['value', 'ref'],
    'additionalProperties': False,
    'properties': {
        'value': {
            'bsonType': 'double',
            'description': 'The value',
        },
        'ref': {
            'bsonType': 'string',
            'description': 'The reference citation for the value',
        },
        'err_low': {
            'bsonType': 'double',
            'description': 'The lower error for the value',
        },
        'err_high': {
            'bsonType': 'double',
            'description': 'The upper error for the value',
        },
        'err': {
            'bsonType': 'string',
            'description': 'The formated error values as a string',
        }
    },
}
single_star_param_int = {
    'bsonType': 'object',
    'description': 'The curated data object for a single-star stellar-parameter',
    'required': ['value', 'ref'],
    'additionalProperties': False,
    'properties': {
        'value': {
            'bsonType': 'int',
            'description': 'The value',
        },
        'ref': {
            'bsonType': 'string',
            'description': 'The reference citation for the value',
        },
        'err_low': {
            'bsonType': 'int',
            'description': 'The lower error for the value',
        },
        'err_high': {
            'bsonType': 'int',
            'description': 'The upper error for the value',
        },
        'err': {
            'bsonType': 'string',
            'description': 'The formated error values as a string',
        }
    },
}


single_star_param_str = {
    'bsonType': 'object',
    'description': 'The curated data object for a single-star stellar-parameter',
    'required': ['value', 'ref'],
    'additionalProperties': False,
    'properties': {
        'value': {
            'bsonType': 'string',
            'description': 'The value',
        },
        'ref': {
            'bsonType': 'string',
            'description': 'The reference citation for the value',
        },
    },
}


single_params = [single_star_param_double, single_star_param_int, single_star_param_str]

indexed_name_types = ['hip', 'hd', 'tyc', 'gaia dr1', 'gaia dr2', 'gaia dr3', 'bd', '2mass', 'koi', 'kepler', 'wds']
index_props = {name_type: {'bsonType': ['string', 'null'],
                           'description': f'must be a string and is not required'}
               for name_type in indexed_name_types + ['nea']}
indexed_name_types = set(indexed_name_types)

validator_star_doc = {
    'bsonType': 'object',
    'title': 'The validator schema for the StarName class',
    'required': ['_id', 'attr_name', 'origin', 'timestamp', 'aliases'],
    'properties': {
        '_id': {
            'bsonType': 'string',
            'description': 'must be a string and is required and unique'
        },
        'attr_name': {
            'bsonType': 'string',
            'description': 'must be a string and is required'
        },
        'origin': {
            'bsonType': 'string',
            'description': 'must be a string and is required'
        },
        'upload_by': {
            'bsonType': 'string',
            'description': 'must be a string and is required'
        },
        'timestamp': {
            'bsonType': 'double',
            'description': 'must be a double and is required'
        },
        'ra': {
            'bsonType': 'double',
            'description': 'must be a double and is not required'
        },
        'dec': {
            'bsonType': 'double',
            'description': 'must be a double and is not required'
        },
        'hmsdms': {
            'bsonType': 'string',
            'description': 'must be a string and is not required'
        },
        'coord_bibcode': {
            'bsonType': 'string',
            'description': 'must be a string and is not required'
        },
        **index_props,
        'aliases': {
            'bsonType': 'array',
            'minItems': 1,
            'uniqueItems': True,
            'description': 'must be an array of string names that this star is known by',
            'items': {
                'bsonType': 'string',
                'description': 'must be a string star name',
            },
        },
        'match_names': {
            'bsonType': 'array',
            'minItems': 1,
            'uniqueItems': True,
            'description': 'must be an array of string names that this star is known by',
            'items': {
                'bsonType': 'string',
                'description': 'must be a blank space removed low-case string star names ',
            },
        },
        'params': {
            'bsonType': 'object',
            'description': 'An object with all the per-star data for a single star',
            'additionalProperties': False,
            'patternProperties': {
                '.+': {'oneOf': single_params},
            },
        },
    },
    'additionalProperties': False,
}