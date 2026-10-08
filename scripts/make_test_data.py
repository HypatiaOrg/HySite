"""Export a small, consistent sample of the HySite database for testing.

The update workflow runs the whole site against this sample in a local MongoDB container, so it
needs no access to the production database. Rerun this when the database structure changes:

    docker compose exec -T django-api python - < scripts/make_test_data.py > mongo/test_data/test_data.json

It runs inside the backend container so it uses the same connection settings as the site.
Only reads are made. Output is MongoDB Extended JSON: {"<database>.<collection>": [documents]}.

The sample keeps:
  - the one summary document, complete (the backend reads it at import and needs every field)
  - STARS_WITH_PLANETS + STARS_WITHOUT_PLANETS documents from hypatiaDB, chosen in _id order
    (repeatable) from documents smaller than MAX_STAR_BYTES, all with absolute abundances
  - the metadata.nea entries for the planet hosts that were kept
metadata.stars and metadata.tic are left empty; the site only needs them to exist.
"""
import os
import sys

import pymongo
from bson import json_util

# the hypatia package prints start-up messages; keep them out of the JSON on stdout
json_out, sys.stdout = sys.stdout, sys.stderr
from hypatia.configs.env_load import connection_string, CLIENT_TLS  # noqa: E402

STARS_WITH_PLANETS = 15
STARS_WITHOUT_PLANETS = 15
MAX_STAR_BYTES = 40_000

client = pymongo.MongoClient(connection_string, tls=CLIENT_TLS)
public = client[os.environ.get("MONGO_DATABASE", "public")]


def sample_stars(has_planets: bool, count: int) -> list[dict]:
    return list(public.hypatiaDB.aggregate([
        {"$match": {"absolute": {"$exists": True}, "nea.planets": {"$exists": has_planets}}},
        {"$match": {"$expr": {"$lt": [{"$bsonSize": "$$ROOT"}, MAX_STAR_BYTES]}}},
        {"$sort": {"_id": 1}},
        {"$limit": count},
    ]))


stars = sample_stars(True, STARS_WITH_PLANETS) + sample_stars(False, STARS_WITHOUT_PLANETS)
nea_names = [star["nea"]["nea_name"] for star in stars if star.get("nea", {}).get("nea_name")]
data = {
    "public.summary": [public.summary.find_one({"_id": "summary_hypatiacatalog"})],
    "public.hypatiaDB": stars,
    "metadata.nea": list(client.metadata.nea.find({"nea_name": {"$in": nea_names}})),
    "metadata.stars": [],
    "metadata.tic": [],
}
for name, docs in data.items():
    print(f"{name}: {len(docs)} documents", file=sys.stderr)
print(json_util.dumps(data, json_options=json_util.CANONICAL_JSON_OPTIONS), file=json_out)
