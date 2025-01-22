from hypatia.collect import BaseCollection
from hypatia.configs.env_load import MONGO_DATABASE
from hypatia.object_params import expected_params_dict
from hypatia.elements import summary_dict, elements_found
from hypatia.sources.catalogs.ops import export_to_records
from hypatia.sources.catalogs.solar_norm import solar_norm
from hypatia.configs.file_paths import default_catalog_file
from hypatia.elements import element_rank, ElementID, plusminus_error


class SummaryCollection(BaseCollection):
    validator = {
        '$jsonSchema': {
            'bsonType': 'object',
            'title': 'The validator schema for the SummaryStarCollection',
            'required': ['_id'],
            'additionalProperties': True,
            'properties': {
                '_id': {
                    'bsonType': 'string',
                    'description': 'must be a string and is required to be unique'
                },
                'units_and_fields': {
                    'bsonType': 'object',
                    'description': 'must be an object and contains the units and fields data',
                    'additionalProperties': False,
                    'patternProperties': {
                        '.+': {
                            'bsonType': 'object',
                            'description': 'must be a object that describes a parameter',
                            'required': ['units'],
                            'additionalProperties': True,
                            'properties': {
                                'units': {
                                    'bsonType': 'string',
                                    'description': 'must be a string and is required'
                                },
                            },
                        },
                    },
                },
                'chemical_ref': {
                    'bsonType': 'object',
                    'description': 'must be an object and contains the units and fields data',
                    'additionalProperties': False,
                    'patternProperties': {
                        '.+': {
                            'bsonType': 'object',
                            'description': 'must be a object that describes a parameter',
                            'required': ['atomic_number', 'average_mass_amu', 'element_name', 'abbreviation', 'group',
                                         'ionization_energy_ev'],
                            'additionalProperties': True,
                            'properties': {
                                'atomic_number': {
                                    'bsonType': 'int',
                                    'description': 'must be an int for the atomic number of the element'
                                },
                                'average_mass_amu': {
                                    'bsonType': 'double',
                                    'description': 'must be a number for the average mass of the element in atomic mass units'
                                },
                                'element_name': {
                                    'bsonType': 'string',
                                    'description': 'must be a string for the name of the element'
                                },
                                'abbreviation': {
                                    'bsonType': 'string',
                                    'description': 'must be a string for the abbreviation of the element'
                                },
                                'group': {
                                    'bsonType': 'int',
                                    'description': 'must be a int for the group number of the element'
                                },
                                'ionization_energy_ev': {
                                    'bsonType': 'double',
                                    'description': 'must be a number for the ionization energy of the element in electron volts'
                                },
                            },
                        },
                    },
                },
                'chemicals_read': {
                    'bsonType': 'array',
                    'description': 'must be an array of strings',
                    'items': {
                        'bsonType': 'string',
                        'description': 'must be a string for the element abbreviation'
                    },
                },
                'chemicals_uploaded': {
                    'bsonType': 'array',
                    'description': 'must be an array of strings',
                    'items': {
                        'bsonType': 'string',
                        'description': 'must be a string for the element abbreviation'
                    },
                },
                'nlte_uploaded': {
                    'bsonType': 'array',
                    'description': 'must be an array of strings',
                    'items': {
                        'bsonType': 'string',
                        'description': 'must be a string for the element abbreviation'
                    },
                },
                'catalogs': {
                    'bsonType': 'object',
                    'description': 'must be an objects with keys that are the catalog short names and objects that describe the catalog',
                    'additionalProperties': False,
                    'patternProperties': {
                        '.+': {
                            'bsonType': 'object',
                            'description': 'must be an object that describes a catalog',
                            'required': ['author', 'year', 'id', 'original_norm_id'],
                            'additionalProperties': False,
                            'properties': {
                                'author': {
                                    'bsonType': 'string',
                                    'description': 'must be a string for the author of the catalog'
                                },
                                'year': {
                                    'bsonType': 'int',
                                    'description': 'must be a int for the year of the catalog'
                                },
                                'id': {
                                    'bsonType': 'string',
                                    'description': 'must be a string for the short name of the catalog'
                                },
                                'original_norm_id': {
                                    'bsonType': 'string',
                                    'description': 'must be a string for the original norm id of the catalog'
                                },
                            },
                        },
                    },
                },
                'normalizations': {
                    'bsonType': 'object',
                    'description': 'must be an Object with norm_keys at the property',
                    'additionalProperties': False,
                    'patternProperties': {
                        '.+': {
                            'bsonType': 'object',
                            'description': 'must be an Object holding data for a single normalization.',
                            'additionalProperties': False,
                            'required': ['author', 'notes'],
                            'properties': {
                                'notes': {
                                    'bsonType': 'string',
                                    'description': 'Required, must be a string for the notes about the normalization'
                                },
                                'author': {
                                    'bsonType': 'string',
                                    'description': 'must be a string for the author of the normalization'
                                },
                                'year': {
                                    'bsonType': 'int',
                                    'description': 'must be a int for the year of the normalization'
                                },
                                'version': {
                                    'bsonType': 'string',
                                    'description': 'must be a string for the version of the normalization'
                                },
                                'values': {
                                    'bsonType': 'object',
                                    'description': 'must be an object with element_strings that give a solar normalization value',
                                    'additionalProperties': False,
                                    'patternProperties': {
                                        '.+': {
                                            'bsonType': 'double',
                                            'description': 'must be a number for the solar normalization value'
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
                'representative_error': {
                    'bsonType': 'object',
                    'description': 'must be an object with keys that are the element abbreviation and values that are the error',
                    'additionalProperties': False,
                    'patternProperties': {
                        '.+': {
                            'bsonType': 'double',
                            'description': 'must be a number for the error in the solar normalization value'
                        },
                    },
                },
                'ids_with_wds_names': {
                    'bsonType': 'array',
                    'description': 'must be an array of strings',
                    'items': {
                        'bsonType': 'string',
                        'description': 'must be a string for the main identifier of a star that has a WDS name'
                    },
                },
                'ids_with_nea_names': {
                    'bsonType': 'array',
                    'description': 'must be an array of strings',
                    'items': {
                        'bsonType': 'string',
                        'description': 'must be a string for the main identifier of a star that has a NEA name'
                    },
                },
            },
        },
    }

    def get_summary(self, id_name: str = None):
        if id_name is None:
            id_name = 'summary_hypatiacatalog'
        return self.collection.find_one({'_id': id_name})


def upload_summary(found_elements: set[ElementID] = None, found_element_nlte: set[ElementID] = None,
                   catalogs_file_name: str = default_catalog_file, found_catalogs: set[str] = None,
                   found_normalizations: set[str] = None,
                   ids_with_wds_names: set[str] = None, ids_with_nea_names: set[str] = None):
    if found_elements is None:
        found_elements = set()
    if found_element_nlte is None:
        found_element_nlte = set()
    if found_catalogs is None:
        found_catalogs = set()
    if found_normalizations is None:
        found_normalizations = set()
    if ids_with_wds_names is None:
        ids_with_wds_names = set()
    if ids_with_nea_names is None:
        ids_with_nea_names = set()
    summary_db = SummaryCollection(db_name=MONGO_DATABASE, collection_name='summary')
    summary_db.reset()

    catalog_data = export_to_records(catalog_input_file=catalogs_file_name,
                                     requested_catalogs=sorted(found_catalogs) if found_catalogs else None)

    normalizations = solar_norm.to_record(norm_keys=found_normalizations) | \
        {'absolute': {'author': 'Absolute', 'notes': 'This key provides data that is in absolute scale and is not normalized to the Sun.'},
         'original': {'author': 'Original', 'notes': 'This key provides the originally published normalization, but omits data that was originally published as absolute. '}}

    doc = {
        '_id': 'summary_hypatiacatalog',
        'units_and_fields': expected_params_dict,
        'chemical_ref': summary_dict,
        'chemicals_read': [str(el) for el in sorted(elements_found, key=element_rank)],
        'chemicals_uploaded': [str(el) for el in sorted(found_elements, key=element_rank)],
        'nlte_uploaded': [str(ElementID(name_lower=el.name_lower, ion_state=el.ion_state, is_nlte=False))
                          for el in sorted(found_element_nlte, key=element_rank)],
        'catalogs': catalog_data,
        'normalizations': normalizations,
        'representative_error': {str(el_id): error_value for el_id, error_value in plusminus_error.items()},
        'ids_with_wds_names': sorted(ids_with_wds_names),
        'ids_with_nea_names': sorted(ids_with_nea_names),
    }
    summary_db.add_one(doc)


if __name__ == '__main__':
    upload_summary(found_normalizations={'lodders09'})
