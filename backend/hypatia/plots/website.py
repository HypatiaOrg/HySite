import os

# Use a non-interactive backend for matplotlib to avoid issues in headless environments like Alpine Linux Containers
import matplotlib as mplot
mplot.use('Agg')
from hypatia.pipeline.star.db import HypatiaDB
from hypatia.configs.env_load import MONGO_DATABASE
from hypatia.configs.file_paths import output_website_dir
from hypatia.plots.histograms import star_count_per_element_histogram


def abundance_histogram(verbose: bool = False) -> None:
    """
    Generate the chemical abundance histogram the website homepage.
    """
    hypatiaDB = HypatiaDB(db_name=MONGO_DATABASE, collection_name='hypatiaDB')
    filename = os.path.join(output_website_dir, 'abundances.png')
    element_strings, star_counts = zip(*hypatiaDB.get_abundance_count(norm_key='absolute',
                                                                      by_element=True,
                                                                      count_stars=True
                                                                      ).items())
    star_count_per_element_histogram(element_strings=element_strings,
                                     star_counts=star_counts,
                                     filename=filename,
                                     verbose=verbose)



if __name__ == '__main__':
    abundance_histogram(verbose=True)