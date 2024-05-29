from hypatia.elements import element_rank, ElementID
from hypatia.collect import BaseCollection
from hypatia.object_params import expected_params_dict
from hypatia.elements import summary_dict, elements_found


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
                "chemical_ref": {
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
                'chemicals_read': {
                    "bsonType": "array",
                    "description": "must be an array of strings",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string for the element abbreviation"
                    },
                },
                'chemicals_uploaded': {
                    "bsonType": "array",
                    "description": "must be an array of strings",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string for the element abbreviation"
                    },
                },
                'nlte_uploaded': {
                    "bsonType": "array",
                    "description": "must be an array of strings",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string for the element abbreviation"
                    },
                },
                'catalogs': {
                    "bsonType": "array",
                    "description": "must be an array of strings",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string for the catalog name"
                    },
                },
                'normalizations': {
                    "bsonType": "array",
                    "description": "must be an array of strings",
                    "items": {
                        "bsonType": "string",
                        "description": "must be a string for the normalization name"
                    },
                },
            },
        },
    }


def upload_summary(found_elements: set[ElementID] = None, found_element_nlte: set[ElementID] = None,
                   found_catalogs: set[str] = None, found_normalizations: set[str] = None):
    if found_elements is None:
        found_elements = set()
    if found_element_nlte is None:
        found_element_nlte = set()
    if found_catalogs is None:
        found_catalogs = set()
    if found_normalizations is None:
        found_normalizations = set()
    summary_db = SummaryCollection(db_name='public', collection_name='summary')
    summary_db.reset()
    doc = {
        "_id": "summary_hypatiacatalog",
        'units_and_fields': expected_params_dict,
        'chemical_ref': summary_dict,
        'chemicals_read': [str(el) for el in sorted(elements_found, key=element_rank)],
        'chemicals_uploaded': [str(el) for el in sorted(found_elements, key=element_rank)],
        'nlte_uploaded': [str(ElementID(name_lower=el.name_lower, ion_state=el.ion_state, is_nlte=False))
                          for el in sorted(found_element_nlte, key=element_rank)],
        'catalogs': sorted(found_catalogs),
        'normalizations': sorted(found_normalizations),
    }
    summary_db.add_one(doc)


if __name__ == '__main__':
    upload_summary()
