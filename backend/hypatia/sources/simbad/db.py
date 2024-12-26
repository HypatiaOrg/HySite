import time

import pymongo

from hypatia.collect import BaseStarCollection


indexed_name_types = ['hip', 'hd', 'tyc', 'gaia dr1', 'gaia dr2', 'gaia dr3', 'bd', '2mass', 'koi', 'kepler', 'wds']
index_props = {name_type: {"bsonType": ["string", "null"], "description": f"must be a string and is not required"}
               for name_type in indexed_name_types + ['nea']}
indexed_name_types = set(indexed_name_types)

validator_star_doc = {
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


class StarCollection(BaseStarCollection):
    validator = {
        "$jsonSchema": validator_star_doc
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

    def get_ids_for_name_type(self, name_type: str) -> list[str]:
        if name_type not in indexed_name_types:
            raise ValueError(f"{name_type} is not a valid name type.")
        return self.collection.find({name_type: {"$exists": True}}).distinct('_id')

    def update_aliases(self, main_id: str, new_aliases: list[str]) -> pymongo.results.UpdateResult:
        old_doc = self.collection.find_one({"_id": main_id})
        old_aliases = old_doc['aliases']
        new_aliases = sorted(list(set(old_aliases + new_aliases)))
        new_doc = old_doc | {"aliases": new_aliases, "timestamp": time.time()}
        return self.update(main_id=main_id, doc=new_doc)

    def prune_older_records(self, prune_before_timestamp: float) -> pymongo.results.DeleteResult:
        return self.collection.delete_many({"timestamp": {"$lt": prune_before_timestamp}})
