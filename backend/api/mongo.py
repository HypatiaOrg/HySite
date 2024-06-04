from hypatia.pipeline.star.db import HypatiaDB
from hypatia.pipeline.summary import SummaryCollection


"""Hard coded API version 2 configurations"""
norm_props = ['notes', 'author', 'year', 'values']
renamed_norms = {
    'and89': 'anders89',
    'asp05': 'asplund05',
    'asp09': 'asplund09',
    'grv98': 'grevesse98',
    'lod09': 'lodders09',
    'grv07': 'grevesse07'
}
catalog_props = ['author', 'year', 'id', 'original_norm_id']
to_v2_catalog_prop_names = {
    'short': 'id',
    'long': 'author',
    'original_norm_id': 'norm',
    'year': 'year',
}

"""Instances that can get data from the database."""
summary_db = SummaryCollection(db_name='public', collection_name='summary')
hypatiaDB = HypatiaDB(db_name='public', collection_name='hypatiaDB')

"""Use and unpack all database summary information."""
summary_doc = summary_db.get_summary()
# normalizations
normalizations = summary_doc['normalizations']
normalizations_v2 = [{'id': norm_key} | {prop: norm_data[prop] if prop in norm_data.keys() else None
                                         for prop in norm_props}
                     for norm_key, norm_data in normalizations.items()]
# available elemental abundances.
available_elements_v2 = summary_doc['chemicals_uploaded']

# available catalogs
available_catalogs_v2 = [cat_dict for cat_dict in summary_doc['catalogs'].values()]


"""functions to distribute data"""


def get_norm_data(norm_key: str) -> dict:
    if norm_key in renamed_norms:
        norm_key = renamed_norms[norm_key]
    return normalizations[norm_key]



