from hypatia.collect import BaseStarCollection


nea_single_value = {
    'bsonType': 'object',
    'description': 'must be a object',
    'required': ['value'],
    'properties': {
        'value': {
            'bsonType': 'double',
            'description': 'must be a double and is required'
        },
        'err_low': {
            'bsonType': 'double',
            'description': 'must be a double and is not required'
        },
        'err_high': {
            'bsonType': 'double',
            'description': 'must be a double and is not required'
        },
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
        'discovery_method': {
            'bsonType': 'string',
            'description': 'must be a string and is not required'
        },
        'period': nea_single_value,
        'semi_major_axis': nea_single_value,
        'eccentricity': nea_single_value,
        'inclination': nea_single_value,
        'pl_mass': nea_single_value,
        'pl_radius': nea_single_value,
        'pl_rade': nea_single_value,
        'pl_bmasse': nea_single_value,
        'pl_radelim': {
            'bsonType': ['double', 'int'],
            'description': 'must be a double and is not required'
        },
        'radius_gap': {
            'bsonType': 'double',
            'description': 'must be a double and is not required'
        },
        'pl_controv_flag': {
            'bsonType': 'bool',
            'description': 'must be a boolean and is not required'
        },
    },
    'additionalProperties': False,
}


planets_props = {
    'bsonType': 'object',
    'minItems': 1,
    'description': 'must be an object with planet letters as keys',
    'additionalProperties': False,
    'patternProperties': {
        '.+': planet_bson,
    },
}


nea_data = {
    'nea_name': {
        'bsonType': 'string',
        'description': 'must be a string and is required and unique'
    },
    'dist': nea_single_value,
    'mass': nea_single_value,
    'rad': nea_single_value,
    'teff': nea_single_value,
    'planet_letters': {
        'bsonType': 'array',
        'minItems': 1,
        'description': 'must be an array letters for each known planet',
        'items': {
            'bsonType': 'string',
            'description': 'must be a string planet letter',
        },
    },
    'planets': planets_props,
}

validator = {
    '$jsonSchema': {
        'bsonType': 'object',
        'title': 'The validator schema for the StarName class',
        'required': ['_id', 'attr_name', 'nea_name', 'planet_letters', 'planets'],
        'properties': {
            '_id': {
                'bsonType': 'string',
                'description': 'must be a string and is required and unique'
            },
            'attr_name': {
                'bsonType': 'string',
                'description': 'must be a string and is not required'
            },
            'tic': {
                'bsonType': 'string',
                'description': 'must be a string and is not required'
            },
            'gaia dr2': {
                'bsonType': 'string',
                'description': 'must be a string and is not required'
            },
            'hd': {
                'bsonType': 'string',
                'description': 'must be a string and is not required'
            },
            'hip': {
                'bsonType': 'string',
                'description': 'must be a string and is not required'
            },
            **nea_data,
        },
        'additionalProperties': False,
    }
}


def and_filters(min_value: float | None, max_value: float | None, field_name: str) -> list[dict]:
    and_filters_planetary = []
    if min_value is not None and max_value is not None:
        and_filters_planetary.append({'$or': [
            {f'planets_array.v.{field_name}.value': {'$gte': min_value}},
            {f'planets_array.v.{field_name}.value': {'$lte': max_value}}
        ]})
    elif min_value is not None:
        and_filters_planetary.append({f'planets_array.v.{field_name}.value': {'$gte': min_value}})
    elif max_value is not None:
        and_filters_planetary.append({f'planets_array.v.{field_name}.value': {'$lte': max_value}})
    return and_filters_planetary


class ExoPlanetStarCollection(BaseStarCollection):
    validator = validator

    def create_indexes(self):
        self.collection_add_index(index_name='nea_name', ascending=True, unique=True)
        self.collection_add_index(index_name='tic', ascending=True, unique=False)
        self.collection_add_index(index_name='gaia dr2', ascending=True, unique=False)
        self.collection_add_index(index_name='hd', ascending=True, unique=False)
        self.collection_add_index(index_name='hip', ascending=True, unique=False)
        self.collection_add_index(index_name='planet_letters', ascending=True, unique=False)

    def get_all_stars(self):
        return list(self.collection.find())

    def hysite_api(self, pl_mass_min: float = None, pl_mass_max: float = None,
                   pl_radius_min: float = None, pl_radius_max: float = None):
        # stage 1a: reshape the planetary data to be an array of objects, which can be a targe for unwind
        # stage 1b: unwind the planetary data to allow for per-planet filtering
        json_pipeline = [{'$addFields': {'planets_array': {'$objectToArray': '$planets'}}},
                         {'$unwind': '$planets_array'}]
        # Stage 2: filtering
        and_filters_planetary = []
        and_filters_planetary.extend(and_filters(min_value=pl_mass_min, max_value=pl_mass_max, field_name='pl_mass'))
        and_filters_planetary.extend(and_filters(min_value=pl_radius_min, max_value=pl_radius_max, field_name='pl_radius'))
        if and_filters_planetary:
            # only add a pipline stage if there are filters to apply.
            json_pipeline.append({'$match': {'$and': and_filters_planetary}})
        # # stage 3: group the data back into a single document
        json_pipeline.append({'$group': {
            '_id': '$_id',
            'nea_name': {'$first': '$nea_name'},
            'planets_list': {'$push': '$planets_array.v'},
        }})
        raw_results = list(self.collection.aggregate(json_pipeline))
        return raw_results
