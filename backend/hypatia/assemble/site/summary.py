

from hypatia.collect import BaseCollection
from hypatia.object_params import expected_params_dict


class SummaryCollection(BaseCollection):
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "title": "The validator schema for the SummaryStarCollection",
            "required": ["_id"],
            "additionalProperties": True,
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required to be unique"
                },
                'units_and_fields': {
                    "bsonType": "object",
                    "description": "must be an object and contains the units and fields data",
                    'additionalProperties': False,
                    'patternProperties': {
                        ".+": {
                            "bsonType": "object",
                            "description": "must be a object that describes a parameter",
                            "required": ['units'],
                            "additionalProperties": True,
                            "properties": {
                                "units": {
                                    "bsonType": "string",
                                    "description": "must be a string and is required"
                                },
                            },
                        },
                    },
                },
            },
        },
    }


def upload_summary():
    summary_db = SummaryCollection(db_name='public', collection_name='summary')
    summary_db.reset()
    doc = {
        "_id": "summary_hypatiacatalog",
        'units_and_fields': expected_params_dict
    }
    summary_db.add_one(doc)


if __name__ == '__main__':
    upload_summary()
