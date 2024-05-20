"""
Base class for tables data that use star names as their primary key (unique identifier).
"""
import time

import pymongo

from hypatia.config import connection_string


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
        if unique:
            self.collection.create_index([(index_name, 1 if ascending else -1)], unique=unique)
        else:
            self.collection.create_index([(index_name, 1 if ascending else -1)])

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
