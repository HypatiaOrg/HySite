import time

from pymongo.cursor import Cursor
from pymongo.results import DeleteResult, InsertOneResult


from hypatia.config import current_user
from hypatia.collect import BaseStarCollection
from hypatia.sources.simbad.validator import validator_star_doc, indexed_name_types


def  get_match_name(name: str) -> str:
    return name.replace(' ', '').lower()


class StarCollection(BaseStarCollection):
    validator = {
        '$jsonSchema': validator_star_doc
    }

    def create_indexes(self):
        self.collection_add_index(index_name='ra', ascending=True, unique=False)
        self.collection_add_index(index_name='dec', ascending=True, unique=False)
        for name_type in indexed_name_types:
            self.collection_add_index(index_name=name_type, ascending=True, unique=False)
        self.collection_add_index(index_name='aliases', ascending=True, unique=False)
        self.collection_add_index(index_name='match_names', ascending=True, unique=False)

    def update(self, main_id: str, doc: dict[str, list | str | float]) -> InsertOneResult:
        return self.collection.replace_one({'_id': main_id}, doc)

    def find_name_match(self, name: str | list[str]) -> dict | None:
        if isinstance(name, str):
            names = [name]
        else:
            names = name
        result = self.collection.find_one({'match_names': {'$in': names}})
        if result:
            return result
        else:
            return None

    def find_names_from_expression(self, regex: str) -> Cursor:
        return self.collection.find({'match_names': {'$regex': f'{regex}', '$options': 'i'}})

    def get_ids_for_name_type(self, name_type: str) -> list[str]:
        if name_type not in indexed_name_types:
            raise ValueError(f'{name_type} is not a valid name type.')
        return self.collection.find({name_type: {'$exists': True}}).distinct('_id')

    def update_aliases(self, main_id: str, new_aliases: list[str]) -> dict[str, any]:
        old_doc = self.collection.find_one({'_id': main_id})
        old_aliases = old_doc['aliases']
        new_aliases = sorted(list(set(old_aliases + new_aliases)))
        new_doc = old_doc | {'aliases': new_aliases, 'timestamp': time.time()}
        new_doc['match_names'] = list({get_match_name(name=name) for name in new_aliases})
        new_doc['upload_by'] = current_user
        self.update(main_id=main_id, doc=new_doc)
        return new_doc

    def prune_older_records(self, prune_before_timestamp: float, additional_filter: dict[str, any] | None = None
                            ) -> DeleteResult:
        if additional_filter:
            return self.collection.delete_many({
                'timestamp': {'$lt': prune_before_timestamp},
                **additional_filter
            })
        else:
            return self.collection.delete_many({
                'timestamp': {'$lt': prune_before_timestamp},
            })


if __name__ == '__main__':
    from hypatia.config import MONGO_STARNAMES_COLLECTION
    star_collection = StarCollection(collection_name=MONGO_STARNAMES_COLLECTION)
    star_collection.reset()
