import os
import toml
from hypatia.config import site_dir

element_plusminus_error_file = os.path.join(site_dir, 'element_plusminus_err.toml')


def get_plusminus_error_from_file() -> dict:
    with open(element_plusminus_error_file, 'r') as f:
        return toml.load(f)


plusminus_error = {key.lower(): float(value) for key, value in get_plusminus_error_from_file().items()}


def get_representative_error(element_name: str) -> float:
    return plusminus_error.get(element_name.lower(), 0.001)
