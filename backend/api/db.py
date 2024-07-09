from hypatia.pipeline.star.db import HypatiaDB
from hypatia.pipeline.summary import SummaryCollection


"""Instances that can get data from the database."""
summary_db = SummaryCollection(db_name='public', collection_name='summary')
hypatia_db = HypatiaDB(db_name='public', collection_name='hypatiaDB')
# star_collection = StarCollection(db_name='public', collection_name='stars')

"""Database summary information."""
summary_doc = summary_db.get_summary()
# normalizations
normalizations = summary_doc['normalizations']
# available catalogs
catalogs = summary_doc['catalogs']

