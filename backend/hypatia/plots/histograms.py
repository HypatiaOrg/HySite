import os

import requests
import numpy as np
import matplotlib.pyplot as plt

from hypatia.config import plot_dir, histo_dir
from hypatia.elements import element_rank, ElementID
from hypatia.tools.color_text import file_name_text, colorize_text

colors = ['goldenrod', 'dodgerblue', 'darkorange', 'darkorchid', 'darkgreen']

if not os.path.isdir(plot_dir):
    os.mkdir(plot_dir)
if not os.path.isdir(histo_dir):
    os.mkdir(histo_dir)


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


def star_count_per_element_histogram():
        star_counts_per_element = requests.get(url='https://hypatiacatalog.com/hypatia/api/stats/histogram').json()
        element_strings, star_counts = zip(*star_counts_per_element.items())
        ordered_list_of_bins = get_hist_bins(available_bins=element_strings, is_element_id=True)
        n = len(ordered_list_of_bins)
        hits = [0]
        hits.extend(star_counts)
        ind = np.arange(n)
        width = 0.6
        fig = plt.figure(figsize=(22,6))
        ax = fig.add_subplot(111)
        rects1 = plt.bar(ind, hits, width, color='#4E11B7')
        ax.set_xlabel('Element Abundances in the Hypatia Catalog', fontsize=15)
        ax.set_ylabel('Number of Stars with Measured Element X', fontsize=15)
        ax.set_ylim([0.0, np.max(hits) +1000.])
        ax.set_xlim([0.0, float(n + 1)])
        ax.set_xticks(ind)
        named_list_of_bins = [name.replace('_', '') for name in ordered_list_of_bins]
        names_up_down =[('\n' if ii % 2 == 1 else '') + named_list_of_bins[ii] for ii in range(len(named_list_of_bins))]
        ax.set_xticklabels(names_up_down)
        ax.tick_params(axis='x', which='minor', length=25)
        ax.tick_params(axis='x', which='both', color='darkgrey')
        ax.text(60, 12000, 'FGKM-type Stars Within 500pc: '+str(np.max(hits)), fontsize=23,  fontweight='bold', color='#4E11B7')
        ax.text(60, 10500, 'Literature Sources: +340', fontsize=23,  fontweight='bold', color='#4E11B7')
        ax.text(60, 9000, f'Number of Elements/Species: {len(element_strings)}', fontsize=23,  fontweight='bold', color='#4E11B7')
        autolabel(rects1)
        #ax.show()
        ax.set_aspect('auto')
        name='bigHist-'+str(np.max(hits))+'.pdf'
        file_name = os.path.join(histo_dir, name)
        fig.savefig(file_name)
        print(f'Saved plot to: {file_name_text(file_name)}')
        print('Number of elements: ' + colorize_text(
            text=f' {len(element_strings)} ', style_text='bold', color_text='black', color_background='yellow'))
        return ordered_list_of_bins, fig, ax

if __name__ == '__main__':
    ordered_list_of_bins_hist, fig_hist, ax_hist = star_count_per_element_histogram()
