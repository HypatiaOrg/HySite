import os

from hypatia.config import ref_dir
from hypatia.load.table_read import row_dict

class Xhip:
    def __init__(self, auto_load=False):
        self.xhip_file_name = os.path.join(ref_dir, "xhip.csv")
        self.ref_data = None
        self.comments = None
        self.available_hip_names = None
        if auto_load:
            self.load()

    def load(self):
        """
        X Hip - it has two types of null values 99.99 and ''
        """
        raw_data = row_dict(self.xhip_file_name, key='HIP', delimiter=",", null_value=99.99)
        if "comments" in raw_data.keys():
            self.comments = raw_data['comments']
            del raw_data['comments']
        self.ref_data = {xhip_key: {param_key: raw_data[xhip_key][param_key] for param_key in raw_data[xhip_key].keys()
                                    if raw_data[xhip_key][param_key] != ""} for xhip_key in raw_data.keys()}
        if self.comments is not None:
            self.ref_data["comments"] = self.comments
        self.available_hip_names = set(self.ref_data.keys())

if __name__ == "__main__":
    xhip = Xhip(auto_load=True)