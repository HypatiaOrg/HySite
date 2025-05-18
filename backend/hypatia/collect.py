"""
Base class for tables data that use star names as their primary key (unique identifier).
"""
import time

from pymongo import MongoClient
from pymongo.cursor import Cursor
from pymongo.results import DeleteResult, InsertOneResult, InsertManyResult, UpdateResult
from pymongo.errors import ServerSelectionTimeoutError, CollectionInvalid, OperationFailure


from hypatia.configs.env_load import connection_string

is_read_only_user = False


class BaseCollection:
    client = MongoClient(connection_string)
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'title': 'The validator schema for the base class StarCollection',
            'required': ['_id'],
            'properties': {
                '_id': {
                    'bsonType': 'string',
                    'description': 'must be a string and is required to be unique'
                },
            }
        }
    }
    collation = {'locale': 'en', 'strength': 2}
    name_col = '_id'

    def __init__(self, collection_name: str, db_name: str = 'metadata', verbose: bool = True):
        self.collection_name = collection_name
        self.db_name = db_name
        self.verbose = verbose
        self.db = self.client[db_name]
        self.server_info = None
        self.test_connection()
        self.collection = self.db[self.collection_name]
        self.create_collection()

    def create_indexes(self):
        self.collection_add_index(index_name='_id', unique=True)

    def create_collection(self):
        global is_read_only_user
        if not is_read_only_user:
            try:
                self.db.create_collection(self.collection_name, check_exists=True,
                                          validator=self.validator, collation=self.collation)
            except CollectionInvalid:
                # the collection already exists
                if self.verbose:
                    print(f'Collection {self.collection_name} already exists in database {self.db_name}')
            except OperationFailure:
                is_read_only_user = True
                # this is like a permissions issue, a read-only user is trying to create a collection
                if self.verbose:
                    print(f'Is read only user? Collection initialization failed at {self.db_name}.{self.collection_name}')
            else:
                if self.verbose:
                    print(f'Created collection {self.collection_name} in database {self.db_name}')
                # finish the setup
                self.collection = self.db[self.collection_name]
                self.create_indexes()

    def reset(self):
        self.drop_collection()
        self.create_collection()

    def test_connection(self, tries: int = 10):
        count = 0
        while count < tries:
            try:
                self.server_info = self.client.server_info()
            except ServerSelectionTimeoutError:
                count += 1
                time.sleep(1)
            else:
                if self.verbose:
                    print(f"Connected to MongoDB server version {self.server_info['version']}")
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

    def collection_exists(self):
        return self.collection_name in self.db.list_collection_names()

    def drop_collection(self):
        if self.verbose:
            print(f'Dropping collection {self.collection_name}')
        return self.collection.drop()

    def drop_database(self):
        if self.verbose:
            print(f'Dropping database {self.db_name}')
        return self.db.drop()

    def collection_add_index(self, index_name: str, ascending: bool = True, unique: bool = False):
        if unique and index_name != '_id':
            self.collection.create_index([(index_name, 1 if ascending else -1)], unique=unique)
        else:
            self.collection.create_index([(index_name, 1 if ascending else -1)])

    def collection_compound_index(self, index_dict: dict[str, int], unique: bool = False):
        self.collection.create_index(list(index_dict.items()), unique=unique)

    def add_one(self, doc: dict | list | float | str | int) -> InsertOneResult:
        return self.collection.insert_one(doc)

    def add_many(self, docs: list[dict | list | float | str | int] | Cursor) -> InsertManyResult:
        return self.collection.insert_many(docs)

    def find_one(self, query: dict | None = None) -> dict:
        if query is None:
            return self.collection.find_one()
        else:
            return self.collection.find_one(query)

    def find_all(self, query: dict = None) -> Cursor:
        if query is None:
            return self.collection.find()
        else:
            return self.collection.find(query)

    def find_by_id(self, find_id: str) -> dict:
        return self.collection.find_one({'_id': find_id})

    def remove_by_id(self, remove_id: str) -> DeleteResult:
        return self.collection.delete_one({'_id': remove_id})


class BaseStarCollection(BaseCollection):
    def __init__(self, collection_name: str, db_name: str = 'metadata', name_col: str = '_id', verbose: bool = True):
        super().__init__(collection_name, db_name, verbose)
        self.name_col = name_col

    def create_indexes(self):
        self.collection_add_index(self.name_col, unique=True)

    def update_timestamp(self, update_id: str) -> UpdateResult:
        return self.collection.update({'_id': update_id}, {'$set': {'timestamp': time.time()}})

if __name__ == '__main__':
    test_collection = BaseCollection(db_name='metadata', collection_name='stars')
    collection_found = test_collection.collection_exists()
    print(collection_found)