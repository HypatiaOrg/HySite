from hypatia.sources.collect import BaseCollection
from hypatia.sources.nea.db import nea_data

normalization_handles = ["original", "absolute", "anders89", "asplund05", "asplund09", "grevesse98", "lodders09",
                         "grevesse07"]
single_star_param = {
    "bsonType": "object",
    "description": "The curated data object for a single-star stellar-parameter",
    "required": ["value", "ref"],
    "additionalProperties": False,
    "properties": {
        "value": {
            "bsonType": "double",
            "description": "The value",
        },
        "ref": {
            "bsonType": "string",
            "description": "The reference citation for the value",
        },
        "err_low": {
            "bsonType": "double",
            "description": "The lower error for the value",
        },
        "err_high": {
            "bsonType": "double",
            "description": "The upper error for the value",
        },
    },
}
reduced_abundance = {
    "bsonType": "object",
    "description": "Data for a single reduced chemical-element abundance",
    "required": ["mean", "median"],
    "additionalProperties": False,
    "properties": {
        "mean": {
            "bsonType": "double",
            "description": "must be a double and is required"
        },
        "median": {
            "bsonType": "double",
            "description": "must be a double and is required"
        },
        "plusminus": {
            "bsonType": "double",
            "description": "must be a double and is not required"
        },
        "std": {
            "bsonType": "double",
            "description": "must be a double and is not required"
        },
        "min": {
            "bsonType": "double",
            "description": "must be a double and is not required"
        },
        "max": {
            "bsonType": "double",
            "description": "must be a double and is not required"
        },
        "catalogs": {
            "bsonType": "object",
            "description": "These are the raw values pair with the catalog name of the source",
            "additionalProperties": False,
            "patternProperties": {
                ".+": {
                    "bsonType": "double",
                    "description": "a float value for the abundance",
                }
            }
        },

    },
}

normalizations = {
    "bsonType": "object",
    "description": "The available abundance normalizations",
    "required": normalization_handles,
    "additionalProperties": False,
    "patternProperties": {
        ".+": {
            "bsonType": "object",
            "description": "Normalized chemical-element abundances",
            "additionalProperties": False,
            "patternProperties": {
                ".+": reduced_abundance,
            },
        }
    },
}


class HypatiaRecord(BaseCollection):
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "The validator schema for the StarName class",
            "required": ["_id", "attr_name", "timestamp", "aliases"],
            "description": "This is a Star level record for HypatiaCatalog.com the holds abundance and planetary data.",
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required and unique"
                },
                "attr_name": {
                    "bsonType": "string",
                    "description": "must be a string and is required and unique"
                },
                "timestamp": {
                    "bsonType": "double",
                    "description": "must be a double and is required"
                },
                "ra": {
                    "bsonType": "double",
                    "description": "must be a double and is not required"
                },
                "dec": {
                    "bsonType": "double",
                    "description": "must be a double and is not required"
                },
                "hmsdms": {
                    "bsonType": "string",
                    "description": "must be a string and is not required"
                },
                "aliases": {
                    "bsonType": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "description": "must be an array of string names that this star is known by",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string star name",
                    },
                },
                "stellar": {
                    "bsonType": "object",
                    "description": "An object with all the per-star data for a single star",
                    "additionalProperties": False,
                    "patternProperties": {
                        ".+": {
                            "bsonType": "object",
                            "description": "A data object for a single stellar parameter, such as distance, mass, or radius",
                            "required": ["curated", "all"],
                            "additionalProperties": False,
                            "properties": {
                                "curated": single_star_param,
                                "all": {
                                    "bsonType": "array",
                                    "description": "The data records array for a single-star stellar-parameter",
                                    "minItems": 1,
                                    "items": single_star_param,
                                },
                            },
                        },
                    },
                },
                "nea": {
                    "bsonType": "object",
                    'description': 'The NASA Exoplanet Archive host-level data object',
                    'required': ['nea_name', "planet_letters", "planets"],
                    'properties': nea_data,
                },
                'normalizations': normalizations,
            },
        },
    }

    def create_indexes(self):
        # self.collection_add_index(index_name='_id', ascending=True, unique=True)
        self.collection_add_index(index_name='attr_name', ascending=True, unique=True)
        self.collection_add_index(index_name='ra', ascending=True, unique=False)
        self.collection_add_index(index_name='dec', ascending=True, unique=False)
        self.collection_add_index(index_name='aliases', ascending=True, unique=False)
        # normalization handles
        self.collection_add_index(index_name='normalizations', ascending=True, unique=False)
        # chemical-element names and all nested components
        self.collection_add_index(index_name='normalizations.$**', ascending=True, unique=False)


if __name__ == '__main__':
    hypatiaDB = HypatiaRecord(db_name='public', collection_name='hypatiaDB')
    hypatiaDB.reset()  # WARNING: This will delete all data in the collection
