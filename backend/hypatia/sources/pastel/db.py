from hypatia.collect import BaseStarCollection
from hypatia.sources.pastel.read import requested_params

# Tess Input Catalog
pastel_props = {}
for param in requested_params:
    pastel_props[param] = {
        'bsonType': 'array',
        'description': 'The Array of values for the parameter',
        'items': {
            'bsonType': 'object',
            'required': ['value', 'ref'],
            'description': 'must be an object with the value and ref',
            'properties': {
                'value': {
                    'bsonType': 'double',
                    'description': f'must be a double precision float and is not required'
                },
                'ref': {
                    'bsonType': 'string',
                    'description': f'must be a single precision double and is not required'
                },
            }
        }
    }


class PastelCollection(BaseStarCollection):
    name_col = '_id'
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'title': 'The validator schema for the Pastel parameters for a single star',
            'required': ['_id', 'pastel_ids', 'timestamp', 'data'],
            'additionalProperties': False,
            'properties': {
                '_id': {
                    'bsonType': 'string',
                    'description': 'must be a string and is required and unique'
                },
                'pastel_ids' : {
                    'bsonType': 'array',
                    'description': 'must be an array of strings and is required',
                    'items': {
                        'bsonType': 'string',
                        'description': 'must be a string and is required'
                    }
                },
                'timestamp': {
                    'bsonType': 'double',
                    'description': 'must be a double and is required'
                },
                'data': {
                    'bsonType': 'object',
                    'description': 'must be an object and is not required',
                    'properties': pastel_props,
                },
            }
        }
    }