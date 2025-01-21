import os
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from hypatia.configs.file_paths import working_dir, plot_dir

colors = ['dodgerblue', "goldenrod", 'firebrick', "darkgreen", "darkorchid"]

"""
Put the errorbars in the distance_abundance_data so it unpacks as xdata, ydata, xerror, yerror
The labels could be unpacked the same way too
"""


def make_element_distance_plots(distance_abundance_data, xlimits, ylimits, label_list, xlabel, ylabel, figname,
                                save_figure=True, do_eps=False, do_pdf=True, do_png=False):
    line_list = []
    for index, (x_data, y_data) in list(enumerate(distance_abundance_data)):
        color = colors[index % len(distance_abundance_data)]
        plt.scatter(x_data, y_data, marker='o', s=60, facecolor="None", edgecolor=color, alpha=0.6)
        plt.xlabel(xlabel, fontsize=15)
        plt.ylabel(ylabel, fontsize=15)
        plt.xlim(xlimits)
        plt.ylim(ylimits)


        line_list.append(Line2D(range(10), range(10), marker='o', color=color))


    plt.legend(tuple(line_list), tuple(label_list), numpoints=1, loc=3)

    if save_figure:
        base_name = os.path.join(plot_dir, figname)
        if do_eps:
            plt.savefig(base_name + '.eps')
        if do_pdf:
            plt.savefig(base_name + '.pdf')
        if do_png:
            plt.savefig(base_name + '.png')
    else:
        plt.show()
    return