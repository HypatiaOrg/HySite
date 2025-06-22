from time import time

from standard_lib import standard_output
from hypatia.collect import BaseCollection
from hypatia.pipeline.star.db import HypatiaDB
from hypatia.sources.simbad.db import StarCollection
from hypatia.plots.website import abundance_histogram
from hypatia.pipeline.summary import SummaryCollection
from hypatia.configs.source_settings import norm_keys_default
from hypatia.configs.env_load import MONGO_DATABASE, MONGO_STARNAMES_COLLECTION


def update(norm_keys: list[str] = None, refresh_exo_data: bool = False):
    if norm_keys is None:
        norm_keys = list(norm_keys_default)
    abs_list = []
    if 'absolute' in norm_keys:
        norm_keys.remove('absolute')
        abs_list.append('absolute')
    return standard_output(from_scratch=True, refresh_exo_data=refresh_exo_data,
                           norm_keys=norm_keys, mongo_upload=True)


def copy_collection(CollectionClass: BaseCollection,
                    source_db_name: str, source_collection_name: str,
                    target_db_name: str,  target_collection_name: str):
    start_time = time()
    same_collection_name = source_collection_name == target_collection_name
    if same_collection_name:
        print(f'Publishing {source_collection_name} from {source_db_name} to {target_db_name}')
    else:
        print(f'Publishing {source_db_name}.{source_collection_name} to {target_db_name}.{target_collection_name}')
    source = CollectionClass(collection_name=source_collection_name, db_name=source_db_name)
    target = CollectionClass(collection_name=target_collection_name, db_name=target_db_name)
    target.reset()
    all_data = source.find_all()
    print('Copying documents from source to target')
    target.add_many(all_data)
    delta_time = time() - start_time
    if same_collection_name:
        print(f' {delta_time:.2f} seconds to complete the publishing {source_collection_name} from '
              f'{source_db_name} to {target_db_name}')
    else:
        print(f' {delta_time:.2f} seconds to complete the publishing from '
              f'{source_db_name}.{source_collection_name} to {target_db_name}.{target_collection_name}')


def publish_hypatia(target_db_name: str = 'public', source_db_name: str = MONGO_DATABASE):
    for collection_name, CollectionClass in [('hypatiaDB', HypatiaDB), ('summary', SummaryCollection)]:
        copy_collection(CollectionClass=CollectionClass,
            source_db_name=source_db_name, source_collection_name=collection_name,
            target_db_name=target_db_name, target_collection_name=collection_name)

def publish_stars(target_db_name: str = 'stars', source_db_name: str = MONGO_STARNAMES_COLLECTION,
                  remove_docs_with_exceptions: bool = False):
        copy_collection(CollectionClass=StarCollection,
            source_db_name='metadata', source_collection_name=source_db_name,
            target_db_name='metadata', target_collection_name=target_db_name,
            )


def do_website_plots():
    abundance_histogram(verbose=True)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Update the Hypatia database.')
    parser.add_argument('--norm-keys', nargs='*', help='The normalization keys to update.',
                        default=None, dest='norm_keys')
    parser.add_argument('--refresh-exo', action='store_true',
                        help='Refresh the exoplanet data (default), '
                             'this is a slow process that can require user input.',
                        default=True, dest='refresh_exo_data')
    parser.add_argument('--no-refresh-exo', action='store_false',
                        help='Do not refresh the exoplanet data.',
                        dest='refresh_exo_data')
    parser.add_argument('--publish', action='store_true',
                        help='Publish the Hypatia database to the public database. '
                             'If elected all non-publish arguments are ignored. ' 
                             'Data is transferred from a test database to the public database.',
                        default=False)
    parser.add_argument('--publish-stars', action='store_true',
                        help='Publish the Hypatia metadata.stars from another test database.'
                             'If elected all non-publish arguments are ignored. '
                             'data is transferred from a test database default metadata database.',
                        default=False)
    parser.add_argument('--make-website-plots', action='store_true',
                        help='Make the website plots, such as the abundance histogram. '
                             'If selected, all other arguments are ignored.',
                        default=False, dest='make_website_plots')

    args = parser.parse_args()
    if args.make_website_plots:
        do_website_plots()
    elif args.publish or args.publish_stars:
        if args.publish:
            publish_hypatia()
        if args.publish_stars:
            publish_stars()
    else:
        if args.norm_keys:
            norm_keys = args.norm_keys
        else:
            norm_keys = None
        nat_cat, output_star_data, target_star_data = update(norm_keys=norm_keys,
                                                             refresh_exo_data=args.refresh_exo_data)
