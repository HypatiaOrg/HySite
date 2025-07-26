from hypatia.sources.simbad.validator import validator_star_doc, single_params


nea_stellar_or_planetary_params = {
    'bsonType': 'object',
    'description': 'An object with all the per-star data for a single star',
    'additionalProperties': False,
    'patternProperties': {
        '.+': {'oneOf': single_params},
    },
}

catalog_name_value_object = {
    'bsonType': 'object',
    'description': 'These are the raw values pair with the catalog name of the source',
    'additionalProperties': False,
    'patternProperties': {
        '.+': {
            'bsonType': 'double',
            'description': 'a float value for the abundance',
        },
    },
}

single_abundance = {
    'mean': {
        'bsonType': 'double',
        'description': 'must be a double and is required'
    },
    'median': {
        'bsonType': 'double',
        'description': 'must be a double and is required'
    },
    'plusminus': {
        'bsonType': 'double',
        'description': 'must be a double and is not required'
    },
    'std': {
        'bsonType': 'double',
        'description': 'must be a double and is not required'
    },
    'min': {
        'bsonType': 'double',
        'description': 'must be a double and is not required'
    },
    'max': {
        'bsonType': 'double',
        'description': 'must be a double and is not required'
    },
    'catalogs': catalog_name_value_object,
    'catalogs_linear': catalog_name_value_object,
    'median_catalogs': {
        'bsonType': 'array',
        'description': 'The catalogs that contain the median value',
        'items': {
            'bsonType': 'string',
            'description': 'The name of the catalog',
        },
    },
}

single_abundance_keys = set(single_abundance.keys())
chemical_abundances = {
    'bsonType': 'object',
    'description': 'Chemical-element abundances',
    'additionalProperties': False,
    'patternProperties': {
        '.+': {
            'bsonType': 'object',
            'description': 'Data for a single reduced chemical-element abundance',
            'required': ['mean', 'median'],
            'additionalProperties': False,
            'properties': single_abundance,
        },
    },
}

abundance_normalizations = {
    'bsonType': 'object',
    'description': 'The available abundance normalizations',
    'required': ['original'],
    'additionalProperties': False,
    'patternProperties': {
        '.+': chemical_abundances,
    },
}


planet_bson = {
    'bsonType': 'object',
    'description': 'must be a object that describes a planet',
    'required': ['pl_name', 'letter'],
    'properties': {
        'pl_name': {
            'bsonType': 'string',
            'description': 'must be a string and is required'
        },
        'letter': {
            'bsonType': 'string',
            'description': 'must be a string and is required'
        },
        'pl_controv_flag': {
            'bsonType': 'bool',
            'description': 'must be a boolean and is not required'
        },
        'radius_gap': {
            'bsonType': 'double',
            'description': 'must be a double and is not required'
        },
        'pl_radelim': {
            'bsonType': ['double', 'int'],
            'description': 'must bea double and is not required'
        },
        'planetary': nea_stellar_or_planetary_params,
    },
    'additionalProperties': False,
}


nea_data = {
    'nea_name': {
        'bsonType': 'string',
        'description': 'must be a string and is required and unique'
    },
    'stellar': nea_stellar_or_planetary_params,
    'planet_letters': {
        'bsonType': 'array',
        'minItems': 1,
        'description': 'must be an array letters for each known planet',
        'items': {
            'bsonType': 'string',
            'description': 'must be a string planet letter',
        },
    },
    'planets': {
        'bsonType': 'object',
        'minItems': 1,
        'description': 'must be an object with planet letters as keys',
        'additionalProperties': False,
        'patternProperties': {
            '.+': planet_bson,
        },
    },
}

validator = {
    '$jsonSchema': {
        'bsonType': 'object',
        'title': 'The validator schema for the StarName class',
        'required': ['_id', 'attr_name', 'timestamp'],
        'description': 'This is a Star level record for HypatiaCatalog.com the holds abundance and planetary data.',
        'properties': {
            '_id': {
                'bsonType': 'string',
                'description': 'must be a string and is required and unique'
            },
            'attr_name': {
                'bsonType': 'string',
                'description': 'must be a string and is required and unique'
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
            'names': validator_star_doc,
            'stellar': {
                'bsonType': 'object',
                'description': 'An object with all the per-star data for a single star',
                'additionalProperties': False,
                'patternProperties': {
                    '.+': {
                        'bsonType': 'object',
                        'description': 'A data object for a single stellar parameter, such as distance, mass, or radius',
                        'required': ['curated', 'all'],
                        'additionalProperties': False,
                        'properties': {
                            'curated': {'oneOf': single_params},
                            'all': {
                                'bsonType': 'array',
                                'description': 'The data records array for a single-star stellar-parameter',
                                'minItems': 1,
                                'items': {'oneOf': single_params},
                            },
                        },
                    },
                },
            },
            'nea': {
                'bsonType': 'object',
                'description': 'The NASA Exoplanet Archive host-level data object',
                'required': ['nea_name', 'planet_letters', 'planets'],
                'properties': nea_data,
            },
            'absolute': chemical_abundances,
            'normalizations': abundance_normalizations,
            'nlte': {
                'required': ['absolute'],
                'description': 'The validator schema for NLTE elements ',
                'properties': {
                    'absolute': chemical_abundances,
                    'normalizations': abundance_normalizations,
                },
            },
            'target_handles': {
                'bsonType': 'array',
                'description': 'The handles of the targets that this star is part of',
                'items': {
                    'bsonType': 'string',
                    'description': 'The handle of a target list that this star is part of',
                },
            },
        },
    },
}
