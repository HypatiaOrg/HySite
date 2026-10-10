"""
Copy the static files and the homepage plots into the volume that nginx serves.

Run once by docker-entrypoint.sh, before gunicorn starts. It used to run from
core/settings.py, which every gunicorn worker imports at boot: with more than
one worker the copies ran at the same time, and a worker crashed when the
other had already deleted a directory it was about to delete.
"""
import os
import shutil
import sys

from hypatia.configs.file_paths import output_website_dir

# written at build time by "manage.py collectstatic" (see Dockerfile)
static_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static_root')
# a volume shared with nginx (see compose.yaml)
app_static_dir = os.path.join('/', 'app', 'static')
app_plots_dir = os.path.join(app_static_dir, 'plots')


def copy_static_files(source_dir: str, target_dir: str) -> None:
    """Replace the contents of target_dir with the contents of source_dir."""
    # delete all files in the target directory
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)
    # copy files from source to target directory
    for item in os.listdir(source_dir):
        source_item = os.path.join(source_dir, item)
        target_item = os.path.join(target_dir, item)
        if os.path.isdir(source_item):
            shutil.copytree(source_item, target_item, dirs_exist_ok=True)
        else:
            shutil.copy2(source_item, target_item)
    print(f'Copied static files from {source_dir} to {target_dir}')


if __name__ == '__main__':
    if not os.path.isdir(app_static_dir):
        print(f'{app_static_dir} not found, nothing to copy (not running in the docker container?)')
        sys.exit(0)
    copy_static_files(source_dir=static_root, target_dir=app_static_dir)
    os.makedirs(app_plots_dir, exist_ok=True)
    copy_static_files(source_dir=output_website_dir, target_dir=app_plots_dir)
