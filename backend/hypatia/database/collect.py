"""
Base and child classes for tables data that has star names as the primary key.
"""
import time

import pymongo

from hypatia.config import connection_string


""" Base class """


class BaseCollection:
    client = pymongo.MongoClient(connection_string)
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "The validator schema for the base class StarCollection",
            "required": ["_id"],
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required to be unquie"
                },
            }
        }
    }
    collation = {'locale': 'en', 'strength': 2}

    def __init__(self, collection_name: str, db_name: str = 'metadata', name_col: str = "_id", verbose: bool = True):
        self.collection_name = collection_name
        self.db_name = db_name
        self.name_col = name_col
        self.verbose = verbose
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        self.server_info = None
        self.test_connection()

    def create_indexes(self):
        self.collection_add_index(self.name_col, unique=True)

    def reset(self):
        self.drop_collection()
        self.db.create_collection(self.collection_name, validator=self.validator, collation=self.collation)
        self.collection = self.db[self.collection_name]
        self.create_indexes()

    def test_connection(self, tries: int = 10):
        count = 0
        while count < tries:
            try:
                self.server_info = self.client.server_info()
            except pymongo.errors.ServerSelectionTimeoutError:
                count += 1
                time.sleep(1)
            else:
                if self.verbose:
                    print(f'Connected to MongoDB server version {self.server_info["version"]}')
                    print(f'Connected to database {self.db_name} and collection {self.collection_name}')
                break
            time.sleep(5)

    def __enter__(self):
        self.test_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        if self.verbose:
            print('MongoDB connection closed.')
        return False

    def drop_collection(self):
        if self.verbose:
            print(f'Dropping collection {self.collection_name}')
        return self.collection.drop()

    def drop_database(self):
        if self.verbose:
            print(f'Dropping database {self.db_name}')
        return self.db.drop()

    def collection_add_index(self, index_name: str, ascending: bool = True, unique: bool = False):
        self.collection.create_index([(index_name, 1 if ascending else -1)], unique=unique)

    def collection_compound_index(self, index_dict: dict[str, int], unique: bool = False):
        self.collection.create_index(list(index_dict.items()), unique=unique)

    def add_one(self, doc: dict | list | float | str | int) -> pymongo.results.InsertOneResult:
        return self.collection.insert_one(doc)

    def find_one(self, query: dict) -> dict:
        return self.collection.find_one(query)

    def find_all(self, query: dict = None) -> pymongo.cursor.Cursor:
        if query is None:
            return self.collection.find()
        else:
            return self.collection.find(query)

    def find_by_id(self, find_id: str) -> dict:
        return self.collection.find_one({"_id": find_id})

    def remove_by_id(self, remove_id: str) -> pymongo.results.DeleteResult:
        return self.collection.delete_one({"_id": remove_id})

    def update_timestamp(self, update_id: str) -> pymongo.results.UpdateResult:
        return self.collection.update({"_id": update_id}, {"$set": {"timestamp": time.time()}})


""" Child classes """


indexed_name_types = ["hip", 'hd', 'tyc', 'gaia dr1', 'gaia dr2', 'gaia dr3', 'bd', '2mass', 'koi', 'kepler', 'wds']
index_props = {name_type: {"bsonType": ["string", "null"], "description": f"must be a string and is not required"}
               for name_type in indexed_name_types}
indexed_name_types = set(indexed_name_types)


class StarCollection(BaseCollection):
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "The validator schema for the StarName class",
            "required": ["_id", "attr_name", "origin", "timestamp", "aliases"],
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required and unique"
                },
                "attr_name": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
                },
                "origin": {
                    "bsonType": "string",
                    "description": "must be a string and is required"
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
                **index_props,
                "aliases": {
                    "bsonType": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "description": "must be an array of string names that this star is known by",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string star name",
                    },

                }
            },
            "additionalProperties": False,
        }
    }

    def create_indexes(self):
        self.collection_add_index(index_name='ra', ascending=True, unique=False)
        self.collection_add_index(index_name='dec', ascending=True, unique=False)
        for name_type in indexed_name_types:
            self.collection_add_index(index_name=name_type, ascending=True, unique=False)
        self.collection_add_index(index_name='aliases', ascending=True, unique=False)

    def update(self, main_id: str, doc: dict[str, list | str | float]) -> pymongo.results.InsertOneResult:
        return self.collection.replace_one({"_id": main_id}, doc)


    def find_name_match(self, name: str) -> dict | None:
        result = self.collection.find_one({'aliases': {"$in": [name]}})
        if result:
            return result
        else:
            return None

    def find_names_from_expression(self, regex: str) -> pymongo.cursor.Cursor:
        return self.collection.find({'aliases': {"$regex": f"{regex}", "$options": "i"}})


# Tess Input Catalog
primary_values = ["Teff", "logg", "mass", "rad"]
error_values = set()
tic_props = {}
for primary_value in primary_values:
    err_field = f"{primary_value}_err"
    error_values.add(err_field)
    tic_props[primary_value] = {
                    "bsonType": "object",
                    "description": "must be an object and is not required",
                    "properties": {
                        "value": {
                            "bsonType": "double",
                            "description": f"must be a double precision float and is not required"
                        },
                        "err": {
                            "bsonType": "double",
                            "description": f"must be a single precision double and is not required"
                        }
                    }}
primary_values = set(primary_values)


class TICCollection(StarCollection):
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "The validator schema for the StarName class",
            "required": ["_id", "timestamp", 'is_tic'],
            "additionalProperties": False,
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required and unique"
                },
                "timestamp": {
                    "bsonType": "double",
                    "description": "must be a double and is required"
                },
                "is_tic": {
                    "bsonType": "bool",
                    "description": "must be a boolean and is required"
                },
                "data": {
                    "bsonType": "object",
                    "description": "must be an object and is not required",
                    "properties": tic_props,
                }
            }
        }
    }

    def set_null_record(self, star_name: str):
        self.collection.insert_one({"_id": star_name, "is_tic": False, "timestamp": time.time()})

    def set_record(self, star_name: str, tic_data: dict):
        self.collection.insert_one({'_id': star_name, 'is_tic': True, 'timestamp': time.time(), 'data': tic_data})
