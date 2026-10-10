// Load test_data.json into a new, empty MongoDB.
// The mongo image runs this once, from /docker-entrypoint-initdb.d, when the data directory is empty.
// Made by scripts/make_test_data.py; used by compose.test.yaml.
const fs = require('fs');
const data = EJSON.parse(fs.readFileSync('/test_data/test_data.json', 'utf8'), { relaxed: false });
for (const [name, docs] of Object.entries(data)) {
    const [dbName, collectionName] = name.split('.');
    const database = db.getSiblingDB(dbName);
    database.createCollection(collectionName);
    if (docs.length > 0) {
        database.getCollection(collectionName).insertMany(docs);
    }
    print(`Loaded ${docs.length} documents into ${name}`);
}
