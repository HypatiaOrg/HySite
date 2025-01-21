from hypatia.pipeline.star.db import HypatiaDB
from hypatia.configs.env_load import MONGO_DATABASE
from hypatia.sources.simbad.db import StarCollection
from hypatia.sources.tic.db import TICStarCollection
from hypatia.pipeline.summary import SummaryCollection
from hypatia.sources.nea.db import ExoPlanetStarCollection

# Intermediate data that is used to create the final data
star_collection = StarCollection(db_name='metadata', collection_name='stars')
all_star_names = list(star_collection.find_all())

tic_collection = TICStarCollection(db_name='metadata', collection_name='tic')
all_tic_data = list(tic_collection.find_all())

nea_collection = ExoPlanetStarCollection(db_name='metadata', collection_name='nea')
all_nea_data = list(nea_collection.find_all())

# the processed Hypatia Catalog data
hypatiaDB = HypatiaDB(db_name=MONGO_DATABASE, collection_name='hypatiaDB')
all_hypatia_data = list(hypatiaDB.find_all())

summary_collection = SummaryCollection(db_name=MONGO_DATABASE, collection_name='summary')
summary_hypatia_data = list(summary_collection.find_all())[0] # this is a single-element list
