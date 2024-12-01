from time import time
from hypatia.config import MONGO_DATABASE
from hypatia.pipeline.star.db import HypatiaDB


def publish_hypatia(target_db_name: str = 'public', source_db_name: str = MONGO_DATABASE):
    for collection_name in ['hypatiaDB', 'summary']:
        start_time = time()
        print(f'Publishing {collection_name} from {source_db_name} to {target_db_name}')
        source = HypatiaDB(collection_name=collection_name, db_name=source_db_name)
        target = HypatiaDB(collection_name=collection_name, db_name=target_db_name)
        target.drop_collection()
        all_data = source.find_all()
        print('Copying documents from source to target')
        target.add_many(all_data)
        delta_time = time() - start_time
        print(f' {delta_time:.2f} seconds to complete the publishing {collection_name} from {source_db_name} to {target_db_name}')


if __name__ == '__main__':
    publish_hypatia()
