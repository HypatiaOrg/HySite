from warnings import warn

from hypatia.pipeline.star.db import HypatiaDB
from hypatia.pipeline.summary import SummaryCollection
from hypatia.sources.nea.db import ExoPlanetStarCollection


"""Instances that can get data from the database."""
summary_db = SummaryCollection(db_name='public', collection_name='summary')
hypatia_db = HypatiaDB(db_name='public', collection_name='hypatiaDB')
nea_db = ExoPlanetStarCollection(db_name='metadata', collection_name='nea')
# star_collection = StarCollection(db_name='public', collection_name='stars')

"""Database summary information."""
summary_doc = summary_db.get_summary()
# normalizations
normalizations = summary_doc['normalizations']
# available catalogs
catalogs = summary_doc['catalogs']
handle_to_author = {cat_name: cat_doc['author'] for cat_name, cat_doc in catalogs.items()}
author_to_original_handle = {}
original_cat_to_handle_lists = {}
for cat_name, author in handle_to_author.items():
    if '_' in cat_name:
        original_handle, *_ = cat_name.split('_')
    else:
        original_handle = cat_name
    if author in author_to_original_handle.keys():
        if original_handle == author_to_original_handle[author]:
            pass
        else:
            warn(f"Catalog Author {author} is not unique for handles {original_handle} and {author_to_original_handle[author]}")
    else:
        author_to_original_handle[author] = original_handle
    if original_handle not in original_cat_to_handle_lists.keys():
        original_cat_to_handle_lists[original_handle] = []
    original_cat_to_handle_lists[original_handle].append(cat_name)
number_of_catalogs = len(author_to_original_handle.keys())
