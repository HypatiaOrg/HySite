import os
import matplotlib.pyplot as plt
from hypatia.config import plot_dir

colors = ["goldenrod", 'dodgerblue', 'darkorange', "darkorchid", "darkgreen"]

if not os.path.isdir(plot_dir):
    os.mkdir(plot_dir)
hist_plot_dir = os.path.join(plot_dir, 'hist')
if not os.path.isdir(hist_plot_dir):
    os.mkdir(hist_plot_dir)


def simple_hist(x, bins=10, range=None, title=None, x_label=None, y_label=None, color="darkorange", show=False, save=True):
    plt.hist(x, range=range, bins=bins, color=color)
    if title is not None:
        plt.title(title)
    else:
        title = ""
    if x_label is not None:
        plt.xlabel(x_label)
    if y_label is not None:
        plt.ylabel(y_label)

    if show:
        plt.show()
    if save:
        file_name = os.path.join(plot_dir, 'hist', str(title) + "_histogram.pdf")
        plt.savefig(file_name)
        print("Saved plot to:", file_name)
