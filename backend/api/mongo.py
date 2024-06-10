from hypatia.pipeline.star.db import HypatiaDB
from hypatia.sources.simbad.db import StarCollection
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
hypatia_db = HypatiaDB(db_name='public', collection_name='hypatiaDB')
# star_collection = StarCollection(db_name='public', collection_name='stars')

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

# available WDS stars in the database
available_wds_stars = summary_doc['ids_with_wds_names']


"""functions to distribute data"""


def get_norm_data(norm_key: str) -> dict:
    if norm_key in renamed_norms:
        norm_key = renamed_norms[norm_key]
    return normalizations[norm_key]


def get_star_data_v2(star_names: list[str]) -> list[dict]:
    return hypatia_db.star_data_v2(star_names=star_names)


if __name__ == '__main__':
    test_data = get_star_data_v2(star_names=[
        "HIP 12345",
        "HIP 56789",
        "HIP 113044",
        "HIP22453",
        '*6Lyn',
        'hip',
      ])
