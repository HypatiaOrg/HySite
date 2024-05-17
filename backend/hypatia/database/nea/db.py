import pymongo

from hypatia.database.collect import BaseCollection


nea_single_value = {
    "bsonType": "object",
    "description": "must be a object",
    "required": ["value"],
    "properties": {
        "value": {
            "bsonType": "double",
            "description": "must be a double and is required"
        },
        "err_low": {
            "bsonType": "double",
            "description": "must be a double and is not required"
        },
        "err_high": {
            "bsonType": "double",
            "description": "must be a double and is not required"
        },
    },
}


possible_planet_letters = ['b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's',
                           't', 'u', 'v', 'w', 'x', 'y', 'z']
planet_bson = {
    "bsonType": "object",
    "description": "must be a object that describes a planet",
    "required": ['pl_name', 'letter'],
    "properties": {
        "pl_name": {
            "bsonType": "string",
            "description": "must be a string and is required"
        },
        "letter": {
            "bsonType": "string",
            "description": "must be a string and is required"
        },
        "discovery_method": {
            "bsonType": "string",
            "description": "must be a string and is not required"
        },
        "period": nea_single_value,
        "semi_major_axis": nea_single_value,
        "eccentricity": nea_single_value,
        "inclination": nea_single_value,
        "pl_mass": nea_single_value,
        "pl_radius": nea_single_value,
    },
    "additionalProperties": False,
}

all_possible_planets = {letter: planet_bson for letter in possible_planet_letters}

validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "The validator schema for the StarName class",
        "required": ["_id", "nea_name", "attr_name", "planet_letters", "planets"],
        "properties": {
            "_id": {
                "bsonType": "string",
                "description": "must be a string and is required and unique"
            },
            "nea_name": {
                "bsonType": "string",
                "description": "must be a string and is required and unique"
            },
            "attr_name": {
                "bsonType": "string",
                "description": "must be a string and is not required"
            },
            "tic": {
                "bsonType": "string",
                "description": "must be a string and is not required"
            },
            "gaia dr2": {
                "bsonType": "string",
                "description": "must be a string and is not required"
            },
            "hd": {
                "bsonType": "string",
                "description": "must be a string and is not required"
            },
            "hip": {
                "bsonType": "string",
                "description": "must be a string and is not required"
            },
            "dist": nea_single_value,
            "mass": nea_single_value,
            "radius": nea_single_value,
            "planet_letters": {
                "bsonType": "array",
                "minItems": 1,
                "description": "must be an array letters for each known planet",
                "items": {
                    "bsonType": "string",
                    "description": "must be a string planet letter",
                },
            },
            "planets": {
                "bsonType": "object",
                "minItems": 1,
                "description": "must be an object with planet letters as keys",
                "properties": all_possible_planets,
            },
        },
        "additionalProperties": False,
    }
}


class ExoPlanetCollection(BaseCollection):
    validator = validator

    def create_indexes(self):
        self.collection_add_index(index_name='nea_name', ascending=True, unique=True)
        self.collection_add_index(index_name='tic', ascending=True, unique=False)
        self.collection_add_index(index_name='gaia dr2', ascending=True, unique=False)
        self.collection_add_index(index_name='hd', ascending=True, unique=False)
        self.collection_add_index(index_name='hip', ascending=True, unique=False)
        self.collection_add_index(index_name='planet_letters', ascending=True, unique=False)


