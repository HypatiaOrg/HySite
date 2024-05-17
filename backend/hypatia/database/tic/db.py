import time

from hypatia.database.collect import BaseCollection

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


class TICCollection(BaseCollection):
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

    def create_indexes(self):
        self.collection_add_index('_id', unique=True)

    def set_null_record(self, star_name: str):
        self.collection.insert_one({"_id": star_name, "is_tic": False, "timestamp": time.time()})

    def set_record(self, star_name: str, tic_data: dict):
        self.collection.insert_one({'_id': star_name, 'is_tic': True, 'timestamp': time.time(), 'data': tic_data})
