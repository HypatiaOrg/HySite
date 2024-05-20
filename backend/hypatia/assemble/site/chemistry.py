import os
import toml
from hypatia.config import site_dir

element_plusminus_error_file = os.path.join(site_dir, 'element_plusminus_err.toml')


def get_plusminus_error_from_file() -> dict:
    with open(element_plusminus_error_file, 'r') as f:
        return toml.load(f)


if __name__ == '__main__':
    # This is the variable name used in the web2py framework
    COL_REP_PLUSMINUS_ERROR = get_plusminus_error_from_file()
