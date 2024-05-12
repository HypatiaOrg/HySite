import os
import random

import numpy
import matplotlib.pyplot as plt

from hypatia.config import plot_dir

if not os.path.isdir(plot_dir):
    os.mkdir(plot_dir)
xy_plot_dir = os.path.join(plot_dir, 'xy_plot')
if not os.path.isdir(xy_plot_dir):
    os.mkdir(xy_plot_dir)

colors = ['BlueViolet', 'Brown', 'CadetBlue', 'Chartreuse', 'Chocolate', 'Coral', 'CornflowerBlue', 'Crimson', ' Cyan',
          'DarkBlue', 'DarkCyan', 'DarkGoldenRod', 'DarkGreen', 'DarkMagenta', 'DarkOliveGreen', 'DarkOrange',
          'DarkOrchid', 'DarkRed', 'DarkSalmon', 'DarkSeaGreen', 'DarkSlateBlue', 'DodgerBlue', 'FireBrick',
          'ForestGreen',
          'Fuchsia','Gold','GoldenRod','Green','GreenYellow','HotPink','IndianRed','Indigo','LawnGreen',
          'LightCoral','Lime','LimeGreen','Magenta','Maroon', 'MediumAquaMarine','MediumBlue','MediumOrchid',
          'MediumPurple','MediumSeaGreen','MediumSlateBlue','MediumTurquoise','MediumVioletRed','MidnightBlue',
          'Navy','Olive','OliveDrab','Orange','OrangeRed','Orchid','PaleVioletRed','Peru','Pink','Plum','Purple',
          'Red','RoyalBlue','SaddleBrown','Salmon','SandyBrown','Sienna','SkyBlue','SlateBlue','SlateGrey',
          'SpringGreen','SteelBlue','Teal','Tomato','Turquoise','Violet','Yellow','YellowGreen']

ls = ['solid', 'dotted', 'dashed', 'dashdot']
lenls = len(ls)

hatches = ['/', '*', '|', '\\', 'x', 'o', '-', '.', '0', '+']


default_plot_dict = {}

# These can be a list or a single value
random.shuffle(colors)
random.shuffle(hatches)
default_plot_dict['colors'] = colors

default_plot_dict['fmt'] = 'o'
default_plot_dict['markersize'] = 5
default_plot_dict['alpha'] = 1.0
default_plot_dict['ls'] = '-'
default_plot_dict['marker'] = None
default_plot_dict['line_width'] = 1

default_plot_dict['ErrorMaker'] = '|'
default_plot_dict['ErrorCapSize'] = 4
default_plot_dict['Errorls'] = 'None'
default_plot_dict['Errorliw'] = 1
default_plot_dict['xErrors'] = None
default_plot_dict['yErrors'] = None
default_plot_dict['legendAutoLabel'] = True
default_plot_dict['legendLabel'] = ''


# These must be a single value
default_plot_dict['title'] = ''
default_plot_dict['xlabel'] = ''
default_plot_dict['ylabel'] = ''

default_plot_dict['xmax'] = None
default_plot_dict['xmin'] = None
default_plot_dict['ymax'] = None
default_plot_dict['ymin'] = None

default_plot_dict['doLegend'] = False
default_plot_dict['legendLoc'] = 0
default_plot_dict['legendNumPoints'] = 3
default_plot_dict['legendHandleLength'] = 5
default_plot_dict['legendFontSize'] = 'small'

default_plot_dict['save'] = False
default_plot_dict['plot_file_name'] = 'plot'
default_plot_dict['do_pdf'] = True
default_plot_dict['show'] = False
default_plot_dict['clearAtTheEnd'] = True

default_plot_dict['xLog'] = False
default_plot_dict['yLog'] = False


# this definition uses the default values defined above is there is no user defined value in dataDict
def extract_plot_val(plot_dict, valString, listIndex=0, keys=None):
    # extract the plot value for the list or use a the singleton value
    if keys != 'None':
        keys = plot_dict.keys()
    if valString in keys:
        if isinstance(plot_dict[valString], list):
            val = plot_dict[valString][listIndex]
        else:
            val = plot_dict[valString]
    else:
        val = default_plot_dict[valString]
    return val


def quick_plotter(plot_dict):
    keys = plot_dict.keys()
    if 'verbose' in keys:
        verbose = plot_dict['verbose']
    else:
        verbose = True
    if verbose:
        print('Starting the quick plotting program...')

    # decide if the user wants to plot a legend
    if 'doLegend' in keys:
        doLegend = plot_dict['doLegend']
    else:
        doLegend = default_plot_dict['doLegend']
    leglabels = []
    leglines = []

    # plot the lists of data
    for (listIndex, y_data) in list(enumerate(plot_dict['y_data'])):
        # Extract the x data for this plot, or use the length of the y_data to make x array
        if 'x_data' not in keys:
            if verbose:
                print('no axis found, using the length of the y_data')
            x_data = range(len(y_data))
        else:
            x_data = plot_dict['x_data'][listIndex]

        # extract the plot color for this y_data
        if 'colors' in keys:
            if isinstance(plot_dict['colors'], list):
                color = plot_dict['colors'][listIndex]
            else:
                color = plot_dict['colors']
        else:
            color = default_plot_dict['colors'][listIndex]

        # extract the plot line style
        ls = extract_plot_val(plot_dict, 'ls', listIndex, keys=keys)
        # extract the plot line width
        line_width = extract_plot_val(plot_dict, 'line_width', listIndex, keys=keys)
        # extract the plot marker format
        fmt = extract_plot_val(plot_dict, 'fmt', listIndex, keys=keys)
        # exact the marker size
        markersize = extract_plot_val(plot_dict, 'markersize', listIndex, keys=keys)
        # extract the marker transparency
        alpha = extract_plot_val(plot_dict, 'alpha', listIndex, keys=keys)
        # extract the error marker
        ErrorMaker = extract_plot_val(plot_dict, 'ErrorMaker', listIndex, keys=keys)
        # extract the error marker's cap  size
        ErrorCapSize = extract_plot_val(plot_dict, 'ErrorCapSize', listIndex, keys=keys)
        # extract the error marker line style
        Errorls = extract_plot_val(plot_dict, 'Errorls', listIndex, keys=keys)
        # extract the erro marker line width
        Errorliw = extract_plot_val(plot_dict, 'Errorliw', listIndex, keys=keys)

        if doLegend:
            # create the legend line and label
            leglines.append(plt.Line2D(range(10), range(10),
                                       color=color, ls=ls,
                                       line_width=line_width, marker=fmt,
                                       markersize=markersize, markerfacecolor=color,
                                       alpha=alpha))
            leglabels.append(extract_plot_val(plot_dict, 'legendLabel', listIndex, keys=keys))

        # this is where the data is plotted
        if verbose:
            print('plotting data in index', listIndex)

        # plot the y_data in Linear-Linear for this loop
        plt.plot(x_data, y_data, linestyle=ls, color=color,
                 linewidth=line_width, marker=fmt, markersize=markersize,
                 markerfacecolor=color, alpha=alpha)
        # are there errorbars on this plot?
        if (('xErrors' in keys) or ('yErrors' in keys)):

            # extract the x error (default is "None")
            xError = extract_plot_val(plot_dict, 'xErrors', listIndex, keys=keys)
            # extract the y error (default is "None")
            yError = extract_plot_val(plot_dict, 'yErrors', listIndex, keys=keys)
            if (xError is not None) or (yError is not None):
                plt.errorbar(x_data, y_data, xerr=xError, yerr=yError,
                             marker=ErrorMaker, color=color, capsize=ErrorCapSize,
                             linestyle=Errorls, eline_width=Errorliw)


        # options for dyplayining Log plots
        if extract_plot_val(plot_dict, 'xLog', keys=keys):
            plt.xscale('log')
        if extract_plot_val(plot_dict, 'yLog', keys=keys):
            plt.yscale('log')





    # now we will add the title and x and y axis labels
    plt.title(extract_plot_val(plot_dict, 'title', keys=keys))
    plt.xlabel(extract_plot_val(plot_dict, 'xlabel', keys=keys))
    plt.ylabel(extract_plot_val(plot_dict, 'ylabel', keys=keys))

    # now we will make the legend (doLegend is True)
    if doLegend:
        # extract the legend info
        if verbose: print('rendering a legend for this plot')
        legendLoc = extract_plot_val(plot_dict, 'legendLoc', keys=keys)
        legendNumPoints = extract_plot_val(plot_dict, 'legendNumPoints', keys=keys)
        legendHandleLength = extract_plot_val(plot_dict, 'legendHandleLength', keys=keys)
        legendFontSize = extract_plot_val(plot_dict, 'legendFontSize', keys=keys)
        # call the legend command
        plt.legend(leglines, leglabels, loc=legendLoc,
                   numpoints=legendNumPoints, handlelength=legendHandleLength,
                   fontsize=legendFontSize)

    # now we adjust the x and y limits of the plot
    current_xmin, current_xmax = plt.xlim()
    current_ymin, current_ymax = plt.ylim()
    if extract_plot_val(plot_dict, 'xmin', keys=keys) is None:
        xmin = current_xmin
    else:
        xmin = plot_dict["xmin"]
    if extract_plot_val(plot_dict, 'xmax', keys=keys) is None:
        xmax = current_xmax
    else:
        xmax = plot_dict["xmax"]
    if extract_plot_val(plot_dict, 'ymax', keys=keys) is None:
        ymin = current_ymin
    else:
        ymin = plot_dict["ymin"]
    if extract_plot_val(plot_dict, 'ymax', keys=keys) is None:
        ymax = current_ymax
    else:
        ymax = plot_dict["ymax"]
    # set the values
    plt.xlim((xmin, xmax))
    plt.ylim((ymin, ymax))

    # here the plot can be saved
    if extract_plot_val(plot_dict, 'save', keys=keys):
        plot_file_name = extract_plot_val(plot_dict, 'plot_file_name', keys=keys)
        full_plot_file_name = os.path.join(xy_plot_dir, plot_file_name)
        if extract_plot_val(plot_dict, 'do_pdf', keys=keys):
            full_plot_file_name += '.pdf'
        else:
            full_plot_file_name += '.png'
        if verbose:
            print('saving the plot:', full_plot_file_name)
        plt.savefig(full_plot_file_name)

    # here the plot can be shown
    if extract_plot_val(plot_dict, 'show', keys=keys):
        if verbose:
            print('showing the plot in a pop up window')
        plt.show()

    if extract_plot_val(plot_dict, 'clearAtTheEnd', keys=keys):
        plt.clf()
        plt.close('all')
        print("Closing all plots.")
    if verbose:
        print('...the quick plotting program has finished.')
    return plt


def rescale(desired, current, target=None):
    if target is None:
        target = current
    maxDesired = max(desired)
    minDesired = min(desired)
    maxCurrent = max(current)
    minCurrent = min(current)

    rangeDesired = float(maxDesired - minDesired)
    rangeCurrent = float(maxCurrent - minCurrent)

    if rangeCurrent == float(0.0):
        # This is the case where current is an array of all the same number.
        # Here we take the middle value of the desired scale and make an array
        # that is only made up of the middle value.
        middleDesired = (rangeDesired / 2.0) + minDesired
        rescaledTarget1 = (target * float(0.0)) + middleDesired
        return rescaledTarget1
    else:
        # 1) set the minimum value of the current to zero
        rescaledTarget1 = target - minCurrent

        # 2) set the maximum value of the rescaledCurrent1 to 1.0
        # (max of rescaledCurrent2 is 1.0, min is 0.0)
        rescaledTarget2 = rescaledTarget1 / rangeCurrent

        # 3 make the range of rescaledCurrent2 the same as the range of the desired
        # (max of rescaledCurrent3 is rangeDesired, min is zero)
        rescaledTarget3 = rescaledTarget2 * rangeDesired

        # 4 make the min of rescaledCurrent3 equal to the min of desired
        # (max of rescaledCurrent3 is rangeDesired + minDesired = maxDesired, min is minDesired)
        rescaledTarget4 = rescaledTarget3 + minDesired

        return rescaledTarget4



def quickHistograms(dataDict, columns=1, bins=10, keys=None,
                    plot_file_name='hist', save=False, doEps=False, show=True,
                    verbose=True):
    if keys is None:
        keys = list(dataDict.keys())
    if len(keys) < 3:
            columns = 1
    numOfSubPlots = len(keys)
    rows = int(numpy.ceil(float(numOfSubPlots)/float(columns)))
    if columns == 1:
        f, axarr = plt.subplots(rows)
    else:
        f, axarr = plt.subplots(rows, columns)
    f.tight_layout()
    f.set_size_inches(10, 8)
    row = -1
    histDict = {}


    for (keyIndex, key) in list(enumerate(keys)):
        column = keyIndex % columns
        if column == 0:
            row += 1
        hist, bin_edges = numpy.histogram(dataDict[key], bins=bins)
        binCenters = [(bin_edges[n + 1] + bin_edges[n]) / 2.0 for n in range(bins)]
        binWidth = (binCenters[-1] - binCenters[0]) / float(bins)
        histDict[key] = (hist, binCenters)


        xlabel_str = ''
        if key == 'integral':
            xlabel_str += "Integral V * s"
            color = 'dodgerblue'
            hatch = '/'
        elif key == 'fittedCost':
            xlabel_str += "'Cost' of fitting function"
            color = 'Crimson'
            hatch = '*'
        elif key == 'fittedAmp1':
            xlabel_str += "Fitted Amplitude 1"
            color = 'SaddleBrown'
            hatch = '|'
        elif key == 'fittedTau1':
            xlabel_str += "Fitted Tau 1"
            color = 'darkorchid'
            hatch = '\\'
        elif key == 'fittedAmp2':
            xlabel_str += "Fitted Amplitude 2"
            color = 'GoldenRod'
            hatch = 'x'
        elif key == 'fittedTau2':
            xlabel_str += "Fitted Tau 2"
            color = 'firebrick'
            hatch = 'o'
        elif key == 'fittedAmp3':
            xlabel_str += "Fitted Amplitude 3"
            color = 'forestGreen'
            hatch = '-'
        elif key == 'fittedTau3':
            xlabel_str += "Fitted Tau 3"
            color = 'Fuchsia'
            hatch = '+'
        elif key == 'fittedAmp4':
            xlabel_str += "Fitted Amplitude 4"
            color = 'Chocolate'
            hatch = '.'
        elif key == 'fittedTau4':
            xlabel_str += "Fitted Tau 4"
            color = 'Magenta'
            hatch = '0'
        elif key == 'deltaX':
            xlabel_str += "length of trimmed file (s)"
            color = 'DarkOrange'
            hatch = '+'

        else:
            xlabel_str = str(key)
            color = colors[keyIndex]
            hatch = hatches[keyIndex]


        if xlabel_str != '':
            xlabel_str += ' '
        if columns == 1:
            axarr[row].set_title(xlabel_str)
            axarr[row].bar(binCenters, hist, binWidth, color=color, hatch=hatch)
            axarr[row].ticklabel_format(style='sci', axis='x', scilimits=(0,0))
        else:
            axarr[row, column].set_title(xlabel_str)
            axarr[row, column].bar(binCenters, hist, binWidth, color=color, hatch=hatch)
            axarr[row, column].ticklabel_format(style='sci', axis='x', scilimits=(0,0))
    #save the plot
    if save:
        plt.draw()
        if doEps:
            plot_file_name += '.eps'
        else:
            plot_file_name += '.png'
        if verbose:
            print("saving file:", plot_file_name)
        plt.savefig(plot_file_name)


    if show:
        plt.show()

    plt.clf()
    plt.close()
    return histDict



