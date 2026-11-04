import os
import tomllib
from warnings import warn

import numpy as np
import requests

from hypatia.elements import ElementID
from hypatia.configs.env_load import MONGO_DATABASE, DEBUG
from hypatia.pipeline.summary import SummaryCollection
from hypatia.tools.color_text import attention_yellow_text
from hypatia.configs.file_paths import element_plusminus_error_file, representative_error_url

plusminus_error_default = 0.1
plusminus_error_decimals = 2


# the representative error of each element: the plus-minus spread the pipeline gives an abundance whose catalog
# reports none, and the "error" bin width of the website's histograms. The file is part of the HyData data
# repository (HypatiaOrg on GitHub), which the pipeline needs beside this code; the website reads the same table
# from the catalog's summary document in the database, so a missing file is only worth a word with DEBUG on.
if os.path.exists(element_plusminus_error_file):
    with open(element_plusminus_error_file, 'rb') as f:
        plusminus_error = {ElementID.from_str(key): np.round(float(value), decimals=plusminus_error_decimals)
                           for key, value in tomllib.load(f).items()}
else:
    if DEBUG:
        print(f'No representative error file at {element_plusminus_error_file}.\n'
              f'  To run the pipeline, clone the HyData data repository (HypatiaOrg on GitHub) beside the backend;\n'
              f'  the website needs no file: the table is read from the catalog summary in the database.')
    summary_db = SummaryCollection(db_name=MONGO_DATABASE, collection_name='summary')
    if summary_db.collection_exists():
        if DEBUG:
            print('  Loading the representative errors from the database')
        summary_data = summary_db.find_one()
        representative_error = summary_data['representative_error']
        plusminus_error = {ElementID.from_str(key): np.round(float(value), decimals=plusminus_error_decimals)
                            for key, value in representative_error.items()}
    else:
        print('  ' + attention_yellow_text(f'Using representative error file from: {representative_error_url}'))
        response = requests.get(representative_error_url)
        if response.status_code == 200:
            plusminus_error = {ElementID.from_str(key): np.round(float(value), decimals=plusminus_error_decimals)
                               for key, value in response.json().items()}
        else:
            msg = f'No representative errors for the elements: no file at {element_plusminus_error_file}, no catalog\n'
            msg += f'summary in the database "{MONGO_DATABASE}", and {representative_error_url} answered {response.status_code}.\n'
            msg += f'Clone the HyData data repository (HypatiaOrg on GitHub) beside the backend, or point MONGO_HOST at a\n'
            msg += f'database with a built catalog. Continuing with the default of {plusminus_error_default} dex for every element.'
            plusminus_error = {}
            warn(msg)


def get_representative_error(element_id: ElementID) -> float:
    if element_id in plusminus_error.keys():
        # this is the exit if the error was in the file or already loaded for a different ion state or NLTE status.
        return plusminus_error[element_id]
    # test if this element can be found in the error file with a different ion state or NLTE status
    proxy_element = None
    if element_id.is_nlte:
        # test if an LTE version of this element is in the error file
        non_nlte_element_id = ElementID(name_lower=element_id.name_lower, ion_state=element_id.ion_state, is_nlte=False)
        if non_nlte_element_id in plusminus_error:
            proxy_element = non_nlte_element_id
        elif element_id.ion_state is not None:
            # test if an NLTE version of this element is available for a neutral version of this element
            non_nlte_element_id = ElementID(name_lower=element_id.name_lower, ion_state=None, is_nlte=True)
            if non_nlte_element_id in plusminus_error:
                proxy_element = non_nlte_element_id
    if proxy_element is None and element_id.ion_state is not None:
        # if no other solution was found, test if an LTE and electrically-neutral version of this element is available
        non_ion_element_id = ElementID(name_lower=element_id.name_lower, ion_state=None, is_nlte=False)
        if non_ion_element_id in plusminus_error:
            proxy_element = non_ion_element_id
    if proxy_element is None:
        # return the default representative error.
        found_error = plusminus_error_default
        warn(f'Element {element_id} not found in the error file, using default representative error.')
    else:
        found_error = plusminus_error[proxy_element]
        warn(f'Element {element_id} not found in the error file, using proxy representative error for {proxy_element}.')
    # find this faster the next time
    plusminus_error[element_id] = found_error
    return plusminus_error_default

if __name__ == '__main__':
    print(get_representative_error(ElementID.from_str('LaII')))