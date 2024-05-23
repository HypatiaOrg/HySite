from hypatia.collect import BaseCollection
from hypatia.elements import website_chemical_summary
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
                "chemical": {
                    "bsonType": "object",
                    "description": "must be an object and contains the units and fields data",
                    'additionalProperties': False,
                    'patternProperties': {
                        ".+": {
                            "bsonType": "object",
                            "description": "must be a object that describes a parameter",
                            "required": ['atomic_number', "average_mass_amu", 'element_name', 'abbreviation', 'group',
                                         'ionization_energy_ev', 'plusminus'],
                            "additionalProperties": True,
                            "properties": {
                                "atomic_number": {
                                    "bsonType": "int",
                                    "description": "must be an int for the atomic number of the element"
                                },
                                "average_mass_amu": {
                                    "bsonType": "double",
                                    "description": "must be a number for the average mass of the element in atomic mass units"
                                },
                                "element_name": {
                                    "bsonType": "string",
                                    "description": "must be a string for the name of the element"
                                },
                                "abbreviation": {
                                    "bsonType": "string",
                                    "description": "must be a string for the abbreviation of the element"
                                },
                                "group": {
                                    "bsonType": "int",
                                    "description": "must be a int for the group number of the element"
                                },
                                "ionization_energy_ev": {
                                    "bsonType": "double",
                                    "description": "must be a number for the ionization energy of the element in electron volts"
                                },
                                "plusminus": {
                                    "bsonType": "double",
                                    "description": "must be a number for the representative error of the element"
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
        'units_and_fields': expected_params_dict,
        'chemical_ref': website_chemical_summary(),
    }
    summary_db.add_one(doc)


if __name__ == '__main__':
    upload_summary()
