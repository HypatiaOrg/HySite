"""
The main_id, or _id, can be used to link star names across different sources with in the Hypatia databases.
"""
from getpass import getuser

from hypatia.pipeline.star.db import HypatiaDB
from hypatia.sources.simbad.ops import get_main_id
from hypatia.sources.nea.db import ExoPlanetStarCollection

star_list = [
    '2MASSJ04545692-6231205',
    '2MASSJ09423526-6228346',
    '2MASSJ09442986-4546351',
    '2MASSJ15120519-2006307',
    'LTT 1445 A',
    'L 168-9',
    'G162-44',
    'G50-16',
    'GJ1252',
    'GJ4102',
    'GJ436',
    'Gliese486',
    'K2-129',
    'K2-137',
    'K2-239',
    'K2-54',
    'K2-72',
    'L181-1',
    'L231-32',
    'GJ 1132',
    'LHS 1678',
    'GJ 357',
    'L98-59',
    'LHS1140',
    'LHS3844',
    'LP961-53',
    'TOI-269',
    'Wolf437',
]

# Get the main_id for each star, if that star is not found, then we will add it to the sources and create a new main_id.
# An interactive prompt will be displayed if the star is not found in SIMBAD or the name database.
star_list_to_main_id = {}
for star_name in star_list:
    main_id = get_main_id(test_name=star_name, test_origin=getuser(), allow_interaction=True)
    star_list_to_main_id[star_name] = main_id

# This can be used to get Hypatia Catalog data or to get NEA data
hypatiaDB = HypatiaDB(db_name='public', collection_name='hypatiaDB')
neaDB = ExoPlanetStarCollection(db_name='metadata', collection_name='nea')

for star_name, main_id in star_list_to_main_id.items():
    print(f"Star {star_name} has main_id {main_id}")
    hypatia_record = hypatiaDB.find_by_id(main_id)
    print(f'hypatia_record: {hypatia_record}')
    nea_record = neaDB.find_by_id(main_id)
    print(f'nea_record: {nea_record}')
