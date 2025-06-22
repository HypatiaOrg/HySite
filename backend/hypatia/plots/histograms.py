import os
import calendar
from datetime import date

import requests
import numpy as np
import matplotlib.pyplot as plt

from hypatia.elements import element_rank, ElementID
from hypatia.tools.color_text import file_name_text, colorize_text
from hypatia.configs.file_paths import histo_dir, histogram_api_url, db_summery_url

colors = ['goldenrod', 'dodgerblue', 'darkorange', 'darkorchid', 'darkgreen']
hypatia_purple = '#4E11B7'


def simple_hist(x, bins=10, range=None, title=None, x_label=None, y_label=None, color='darkorange', show=False, save=True):
    plt.hist(x, range=range, bins=bins, color=color)
    if title is not None:
        plt.title(title)
    else:
        title = ''
    if x_label is not None:
        plt.xlabel(x_label)
    if y_label is not None:
        plt.ylabel(y_label)

    if show:
        plt.show()
    if save:
        file_name = os.path.join(histo_dir, str(title) + '_histogram.pdf')
        plt.savefig(file_name)
        print(file_name_text(f'Saved plot to: {file_name}'))


def autolabel(rects):
    """ attach some text labels """
    for rect in rects:
        height = rect.get_height()
        if height < 300 and not height == 0.0:
            height1 = height  # + 20.0
        else:
            height1 = height
        plt.text(rect.get_x()+rect.get_width()/2.0, 1.02*height1, '%d' % int(height),
                 ha='center', va='bottom')


def auto_web_labels(rects, text_offset: float = 0.0, label_inverse_point: float = 1000.0):
    """ attach some text labels """
    for rect in rects[1:]:  # skip the first bar, which is always zero
        height = int(rect.get_height())
        label = f'{height}'
        if height > label_inverse_point:
            va = 'top'
            y = height - text_offset
            color = 'cyan'
        else:
            va = 'bottom'
            y = height + text_offset
            color = hypatia_purple
        x= rect.get_x() + (rect.get_width() / 2.0)
        plt.text(x=x, y=y, s=label,
                 ha='center', va=va, size=11, color=color, weight='bold', rotation=90)


def get_hist_bins(available_bins: set[str] | set[ElementID], is_element_id: bool) -> list[str]:
    ordered_list_of_bins = ['']
    if is_element_id:
        # convert all string to ElementID, non-elements will fail
        element_ids = [element if isinstance(element, ElementID) else ElementID.from_str(element)
                       for element in available_bins]
        # Turn the sorted ElementIDs back to strings
        ordered_list_of_bins.extend([str(element_id) for element_id in sorted(element_ids, key=element_rank)])
    else:
        # sort in alphabetical order
        ordered_list_of_bins.extend(sorted(available_bins))
    return ordered_list_of_bins


def get_star_count_per_element_data() -> tuple[list[str], list[int]]:
    star_counts_per_element = requests.get(url=histogram_api_url).json()
    element_strings, star_counts = zip(*star_counts_per_element.items())
    return element_strings, star_counts

def get_summary_data() -> dict:
    """
    Get the summary data from the Hypatia API.
    """
    response = requests.get(url=db_summery_url)
    if response.status_code != 200:
        raise ValueError(f'Error fetching summary data: {response.status_code} - {response.text}')
    return response.json()

def star_count_per_element_histogram(element_strings: list[str], star_counts: list[int], filename: str = None,
                                     web_labels: bool = False, literature_sources: int = None,
                                     verbose: bool = True,) \
        -> tuple[list[str], plt.Figure, plt.Axes]:
    if literature_sources is None:
        literature_sources = "+340"
    ordered_list_of_bins = get_hist_bins(available_bins=set(element_strings), is_element_id=True)
    n = len(ordered_list_of_bins)
    hits = [0]
    hits.extend(star_counts)
    ind = np.arange(n)
    fig = plt.figure(figsize=(22,6))
    left = 0.05
    right = 0.99
    bottom = 0.13
    top = 0.97
    width = right - left
    height = top - bottom
    # I turn the axis frame off. I like my data to look free and run off the page.
    ax = fig.add_axes((left, bottom, width, height), frameon=True)
    rects1 = plt.bar(ind, hits, width, color=hypatia_purple)
    today = date.today()
    month = today.month
    month_name = calendar.month_name[month]
    ax.set_xlabel(f'Element Abundances in the Hypatia Catalog ({month_name} {today.year})', fontsize=15)
    ax.set_ylabel('Number of Stars with Measured Element X', fontsize=15)
    y_min = 0.0
    y_max = np.max(hits) + 1000.0
    y_range = y_max - y_min
    ax.set_ylim((y_min, y_max))
    ax.set_xlim((0.0, n + 1.0))
    ax.set_xticks(ind)
    named_list_of_bins = [name.replace('_', '') for name in ordered_list_of_bins]
    names_up_down =[('\n' if ii % 2 == 1 else '') + named_list_of_bins[ii] for ii in range(len(named_list_of_bins))]
    ax.set_xticklabels(names_up_down)
    ax.tick_params(axis='x', which='minor', length=25)
    ax.tick_params(axis='x', which='both', color='darkgrey')
    ax.text(60, 12000, f'FGKM-type Stars Within 500pc: {np.max(hits)}', fontsize=23,  fontweight='bold', color=hypatia_purple)
    ax.text(60, 10500, f'Literature Sources: {literature_sources}', fontsize=23,  fontweight='bold', color=hypatia_purple)
    ax.text(60, 9000, f'Number of Elements/Species: {len(element_strings)}', fontsize=23,  fontweight='bold', color=hypatia_purple)
    if web_labels:
        auto_web_labels(rects1, text_offset=y_range * 0.008, label_inverse_point=y_range * 0.10)
    else:
        autolabel(rects1)
    #ax.show()
    ax.set_aspect('auto')
    if filename is None:
        name = f'bigHist-{np.max(hits)}.pdf'
        filename = os.path.join(histo_dir, name)
    if filename.endswith('.png'):
        fig.savefig(filename, dpi=300)
    else:
        fig.savefig(filename)
    if verbose:
        print(f'Saved plot to: {file_name_text(filename)}')
        print('Number of elements: ' + colorize_text(
            text=f' {len(element_strings)} ', style_text='bold', color_text='black', color_background='yellow'))
    return ordered_list_of_bins, fig, ax


if __name__ == '__main__':
    from hypatia.configs.file_paths import output_website_dir
    abundance_test = os.path.join(output_website_dir, 'abundances-test.png')
    element_strings, star_counts = get_star_count_per_element_data()
    summary_data = get_summary_data()
    catalogs = summary_data['catalogs']
    unique_sources = set(cat_dict['author'] for cat_dict in catalogs.values())

    ordered_list_of_bins_hist, fig_hist, ax_hist = star_count_per_element_histogram(element_strings=element_strings,
                                                                                    star_counts=star_counts,
                                                                                    filename=abundance_test,
                                                                                    literature_sources=len(unique_sources),
                                                                                    web_labels=True)
