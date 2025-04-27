import sys
import matplotlib as mpl
if sys.platform == 'darwin':
    mpl.use(backend='MACOSX')
else:
    mpl.use(backend='TkAgg')
from matplotlib import pyplot as plt

from hypatia.tools.web_query import get_graph_data

"""
See more input parameter options at https://hypatiacatalog.com/api under the section `GET data`.
"""
xaxis1 = 'Fe'
xaxis2 = 'Mg'
yaxis1 = 'O'
yaxis2 = 'H'
plot_data = get_graph_data(xaxis1=xaxis1, xaxis2=xaxis2, yaxis1=yaxis1, yaxis2=yaxis2)
if plot_data is not None:
    fig, ax = plt.subplots()
    x_handle = f'{xaxis1}'
    if xaxis2 is not None and xaxis2.lower() != 'h':
        x_handle += f'_{xaxis2}'
    y_handle = f'{yaxis1}'
    if yaxis2 is not None and yaxis2.lower() != 'h':
        y_handle += f'_{yaxis2}'
    ax.scatter(plot_data[x_handle], plot_data[y_handle])
    ax.set_xlabel(f'[{xaxis1} / {xaxis2}]')
    ax.set_ylabel(f'[{yaxis1} / {yaxis2}]')
    plt.show()
