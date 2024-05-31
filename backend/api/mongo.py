from hypatia.pipeline.star.db import HypatiaDB
from hypatia.pipeline.summary import SummaryCollection


summary_db = SummaryCollection(db_name='public', collection_name='summary')
hypatiaDB = HypatiaDB(db_name='public', collection_name='hypatiaDB')

norm_props = ['notes', 'author', 'year', 'version', 'values']
renamed_norms = {
    'and89': 'anders89',
    'asp05': 'asplund05',
    'asp09': 'asplund09',
    'grv98': 'grevesse98',
    'lod09': 'lodders09',
    'grv07': 'grevesse07'
}

summary_doc = summary_db.get_summary()
normalizations = summary_doc['normalizations']
normalizations_v2 = [{'identifier': norm_key} | {prop: norm_data[prop] if prop in norm_data.keys() else None
                                                 for prop in norm_props}
                     for norm_key, norm_data in normalizations.items()]


def get_norm_data(norm_key: str) -> dict:
    if norm_key in renamed_norms:
        norm_key = renamed_norms[norm_key]
    return normalizations[norm_key]



