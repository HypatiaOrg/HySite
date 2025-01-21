import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

from hypatia.configs.file_paths import plot_dir


def default_margins(bin_left, bin_right, bin_number, margins, data):
    if bin_right is None:
        the_max = np.max(data)+margins
        bin_right = the_max
    else:
        the_max = bin_right+margins
    if bin_left is None:
        the_min = np.min(data)
        bin_left = the_min
    else:
        the_min = bin_left
    the_range = the_max - the_min
    #extra_x_margin = the_range + margins
    #if bin_left is None:
    #    bin_left = the_min - extra_x_margin
    #if bin_right is None:
    #    bin_right = the_max + extra_x_margin
    bin_width = the_range / float(bin_number)
    bins = np.arange(the_min, the_max + (bin_width / 2.0), bin_width)
    return bin_left, bin_right, bins, bin_width



def histPlot(xdata, ydata, exoXdata=None, exoYdata=None, xerror=None, yerror=None, linecolor='firebrick',
             addedScatterX=0, addedScatterY=0, xxlabel="", yylabel="",
             xbinLeft=None, xbinRight=None, ybinLeft=None, ybinRight=None,
             x_bin_number=10, y_bin_number=10, redfield_ratios=False,
             saveFigure=False, figname='plots', do_eps=False, do_pdf=False, do_png=True):
    """
        xbinLeft/xbinRight = the max and min, respectively, range on the x-axis for the scatter plot
        ybinLeft/ybinRight = the max and min, respectively, range on the y-axis for the scatter plot
        binwidthXaxis = the x-axis (top) bin width
        binwidthYaxis = the y-axis (right) bin width
        xdata = list of data to go on the x-axis
        ydata = list of data to go on the y-axis (same length as xdata)
        linecolor = string indicating color of the symbols and histogram lines
        addedScatterX/addedScatterY = shift the range on the x- and y-axis, respectively, to aesthetically remove
           outliers (put in a negative value) or add additional room (for example for the legend)
        xxlabel/yylabel = string for the label on the x-axis or y-axis
        saveFigure = "Y" or "N" flag on whether or not the figure will be saved
        figname = string (without suffixes such as .pdf or .jpg) to indicate figure name
        
        This definition has been simplified from taking multiple stellar populations, such as stars with planets and
        stars without, to looking only at one population. To increase the number of populations, the
        (norm)histX/(norm)histY and axHistx.bar/axHisty.barh calls, with adding respective input parameters, will
        need to be repeated for the additional stellar populations (I included them under a "plotexo" flag).
    """
    xbinl, xbinr, binsx, binwidthx = default_margins(xbinLeft, xbinRight, x_bin_number, addedScatterX, xdata)
    ybinl, ybinr, binsy, binwidthy = default_margins(ybinLeft, ybinRight, y_bin_number, addedScatterY, ydata)
    
    # Python's histogram has no way to normalize the maximum bin to == 1, so
    # first you have to calculate the histogram, take the first element of
    # that object (which shows the count, the second element has the bins)
    # and normalize the bins so the max is 1.
    histX = np.histogram(xdata, bins=binsx)
    normHistX = histX[0] / np.max(histX[0])
    
    histY = np.histogram(ydata, bins=binsy)
    normHistY = histY[0] / np.max(histY[0])

    # Star the process for plotting
    plt.clf()
    nullfmt   = NullFormatter()

    # definitions for the axes
    left, width = 0.123, 0.65  # 1.3 for extended width
    bottom, height = 0.11, 0.65
    bottom_h = left_h = left + width + 0.02    # bottom_h = left+(width*0.5)+0.02 for extended
                                          # left_h = left + width + 0.02


    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom_h, width, 0.2]
    rect_histy = [left_h, bottom, 0.2, height]
    
    # start with a rectangular Figure
    plt.figure(1, figsize=(8, 8))
    
    # Define the parameters/locations for the plotting.
    axScatter = plt.axes(rect_scatter)
    axHistx = plt.axes(rect_histx)
    axHisty = plt.axes(rect_histy)
    
    # no labels on the overlapping axes
    axHistx.xaxis.set_major_formatter(nullfmt)
    axHisty.yaxis.set_major_formatter(nullfmt)
    
    # Make the scatter plot.
    axScatter.scatter(xdata, ydata, s=60, facecolor="None", edgecolor=linecolor, label="stars")
    #axScatter.errorbar(addedScatterX+(xbinRight*0.9), (addedScatterY+ybinRight)-(ybinRight*0.85), xerr=xerror*0.5, yerr=yerror*0.5, marker='|',color='black', capsize=3,linestyle='None')
    if exoXdata:
        axScatter.scatter(exoXdata, exoYdata, s=60, marker="^", facecolor="None", edgecolor="black", label="stars with planets")

    if redfield_ratios:
        # plankton, Earth's crust, bulk, Sun
        #redfield = {"CN": [6.63, 30.5, 536., 4.],
        #            "NP": [16., 0.1, 0.03, 566.],
        #            "CP": [106., 1.7, 18., 2238.],
        #            "CSi": [2.12, 0.0063, 4853., 16.8],
        #            "NSi": [0.32, 0.0002, 9., 4.24],
        #            "PSi": [0.02, 0.0036, 276., 0.0075]}

        # plankton, Earth's crust, bulk Si Earth, bulk Si Mars, Sun
        CNred = [6.63, 11.66, 70.0, 23.3, 3.96]
        CPred = [106., 0.49, 3.4, 0.11, 2233.]
        NPred = [16., 0.042, 0.05, 0.0048, 564.]
        NCred = [0.15, 0.086, 0.014, 0.043, 0.25]
        #PNred = [0.063, 17.6. 20.3. 209.15. 0.0018]
        PCred = [0.009, 2.036, 0.29, 8.97, 0.00045]
        CSired = [7.07, 0.002, 0.0013, 0.0003, 16.8]
        NSired = [1.07, 0.0001, 0.000019, 0.000011, 4.25]
        PSired = [0.67, 0.003, 0.004, 0.0023, 0.0075]

        axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)

        if (xxlabel == "C/N" and yylabel == "C/P"):
            axScatter.scatter(CNred[0], CPred[0], s=100, marker="$\clubsuit$", facecolor="xkcd:leaf green",
                              edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(CNred[1], CPred[1], s=90, marker="$\cap$", color="xkcd:reddish brown",
                              label="Earth's crust")  # crust
            axScatter.scatter(CNred[2], CPred[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(CNred[3], CPred[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(CNred[4], CPred[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)
            axScatter.errorbar(addedScatterX + (xbinRight * 0.9), (addedScatterY + ybinRight) - (ybinRight * 0.85),
                               xerr=xerror * 0.5, yerr=yerror * 0.5, marker='|', color='black', capsize=3,
                               linestyle='None')
        elif (xxlabel == "N/C" and yylabel == "P/C"): ##
            axScatter.scatter(NCred[0], PCred[0], s=100, marker="$\clubsuit$", facecolor="xkcd:leaf green",
                              edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(NCred[1], PCred[1], s=90, marker="$\cap$", color="xkcd:reddish brown", label="Earth's crust")  # crust
            axScatter.scatter(NCred[2], PCred[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(NCred[3], PCred[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(NCred[4], PCred[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)
            axScatter.errorbar(addedScatterX + (xbinRight * 0.9), (addedScatterY + ybinRight) - (ybinRight * 0.85),
                               xerr=xerror * 0.5, yerr=yerror * 0.5, marker='|', color='black', capsize=3,
                               linestyle='None')
        elif (xxlabel == "P/C" and yylabel == "N/C"): ##
            axScatter.scatter(PCred[0], NCred[0], s=100, marker="$\clubsuit$", facecolor="xkcd:leaf green",
                              edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(PCred[1], NCred[1], s=90, marker="$\cap$", color="xkcd:reddish brown", label="Earth's crust")  # crust
            axScatter.scatter(PCred[2], NCred[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(PCred[3], NCred[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(PCred[4], NCred[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)
            axScatter.errorbar(addedScatterX + (xbinRight * 0.9), (addedScatterY + ybinRight) - (ybinRight * 0.85),
                               xerr=xerror * 0.5, yerr=yerror * 0.5, marker='|', color='black', capsize=3,
                               linestyle='None')
        elif (xxlabel == "C/N" and yylabel == "N/P"):
            axScatter.scatter(CNred[0], NPred[0], s=100, marker="$\clubsuit$", facecolor="xkcd:leaf green", edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(CNred[1], NPred[1], s=90, marker="$\cap$", color="xkcd:reddish brown", label="Earth's crust")  # crust
            axScatter.scatter(CNred[2], NPred[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(CNred[3], NPred[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(CNred[4], NPred[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)
        elif (xxlabel == "C/Si" and yylabel == "C/P"):
            axScatter.scatter(CSired[0], CPred[0], s=100, marker="$\clubsuit$", facecolor="xkcd:leaf green", edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(CSired[1], CPred[1], s=90, marker="$\cap$", color="xkcd:reddish brown", label="Earth's crust")  # crust
            axScatter.scatter(CSired[2], CPred[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(CSired[3], CPred[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(CSired[4], CPred[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='lower right', scatterpoints=1, fontsize=8)
            axScatter.errorbar(addedScatterX + (xbinRight * 0.9), addedScatterY + (ybinRight * 0.9),
                               xerr=xerror * 0.5, yerr=yerror * 0.5, marker='|', color='black', capsize=3,
                               linestyle='None')
        elif (xxlabel == "Si/C" and yylabel == "P/C"): ##
            axScatter.scatter(1./CSired[0], PCred[0], s=100, marker="$\clubsuit$", facecolor="xkcd:leaf green",
                              edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(1./CSired[1], PCred[1], s=90, marker="$\cap$", color="xkcd:reddish brown",
                              label="Earth's crust")  # crust
            axScatter.scatter(1./CSired[2], PCred[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(1./CSired[3], PCred[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(1./CSired[4], PCred[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)
            axScatter.errorbar((xbinRight) - (xbinRight * 0.95), addedScatterY + (ybinRight * 0.9),
                               xerr=xerror * 0.5, yerr=yerror * 0.5, marker='|', color='black', capsize=3,
                               linestyle='None')
        elif (xxlabel == "C/Si" and yylabel == "N/Si"): ##
            axScatter.scatter(CSired[0], NSired[0], s=100, marker="$\clubsuit$", facecolor="xkcd:jungle green", edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(CSired[1], NSired[1], s=90, marker="$\cap$", color="xkcd:reddish brown", label="Earth's crust")  # crust
            axScatter.scatter(CSired[2], NSired[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(CSired[3], NSired[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(CSired[4], NSired[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)
            axScatter.errorbar( (xbinRight) - (xbinRight * 0.99), addedScatterY + (ybinRight * 0.9),
                               xerr=xerror * 0.5, yerr=yerror * 0.5, marker='|', color='black', capsize=3,
                               linestyle='None')
        elif (xxlabel == "P/Si" and yylabel == "N/Si"): ##
            axScatter.scatter(PSired[0], NSired[0], s=100, marker="$\clubsuit$", facecolor="xkcd:leaf green", edgecolor="black", label="plankton")  # plankton
            axScatter.scatter(PSired[1], NSired[1], s=90, marker="$\cap$", color="xkcd:reddish brown", label="Earth's crust")  # crust
            axScatter.scatter(PSired[2], NSired[2], s=100, marker="$\oplus$", color="xkcd:reddish brown", label = "bulk silicate Earth")  #bulk = mantle+core
            axScatter.scatter(PSired[3], NSired[3], s=100, marker="$\u2642$", color="red", label="bulk silicate Mars")  # Mars
            axScatter.scatter(PSired[4], NSired[4], s=100, marker="$\odot$", color="goldenrod", label="Sun")  # Sun
            axScatter.legend(loc='upper right', scatterpoints=1, fontsize=8)
            axScatter.errorbar(addedScatterX + (xbinRight * 0.9), (addedScatterY + ybinRight) - (ybinRight * 0.85),
                               xerr=xerror * 0.5, yerr=yerror * 0.5, marker='|', color='black', capsize=3,
                               linestyle='None')

    # Set the limits on the scatter plot.
    axScatter.set_xlim([xbinl, xbinr+addedScatterX])
    axScatter.set_ylim([ybinl, ybinr+addedScatterY])


    # Make the bar plots. Note that the horizontal one is barh.
    axHistx.bar(binsx[:-1], normHistX, binwidthx, facecolor="None",
                edgecolor=linecolor, align='edge')
    axHisty.barh(binsy[:-1], normHistY, binwidthy, facecolor="None",
                 edgecolor=linecolor, align='edge')

    axHistx.set_xlim(axScatter.get_xlim())
    axHisty.set_ylim(axScatter.get_ylim())
    
    # Adapt the labeling based on what's being plotted.
    axScatter.set_xlabel(xxlabel, fontsize=15)
    axScatter.set_ylabel(yylabel, fontsize=15)

    # # Histograms for the exoplanet host stars on the x- and y-axes
    # exohistX = np.histogram(exoXdata, bins=binsx)
    # exonormHistX = []
    # for num in exohistX[0]:
    #     exonormHistX.append(float(num) / float(max(exohistX[0])))
    #
    # exohistY = np.histogram(exoYdata, bins=binsy)
    # exonormHistY = []
    # for num in exohistY[0]:
    #     exonormHistY.append(float(num) / float(max(exohistY[0])))
    #
    # axHistx.bar(binsx[:-1], exonormHistX, binwidthx, facecolor="None", edgecolor='black', align='edge')
    # axHisty.barh(binsy[:-1], exonormHistY, binwidthy, facecolor="None", edgecolor='black', align='edge')
    
    axHistx.set_ylabel("Relative Dist.", fontsize=9)
    axHisty.set_xlabel("Relative Distribution", fontsize=9)



    if saveFigure:
        base_name = os.path.join(plot_dir, figname)
        if do_eps:
            plt.savefig(base_name + '.eps', bbox_inches='tight')
        if do_pdf:
            plt.savefig(base_name + '.pdf', bbox_inches='tight')
        if do_png:
            plt.savefig(base_name + '.png', bbox_inches='tight')
    else:
        plt.show()
    return


if __name__ == "__main__":
    """
    Example of what the data looks like in the Hypatia 2.0 so that it's run-able for [C/N] and [C/P]
    
    To get the data to this point I: found which stars had all three elements (C, N, P), flattened the XH data for those 
    stars by taking the median values for those stars that had multiple measurements, and then calculated the 
    [C/H]-[N/H] = [C/N] and [C/H]-[P/H] = [C/P] which is below
    """

    medCN = [3.890451449942805, 2.6915348039269085, 8.51138038202376, 12.589254117941662, 5.0699070827470445, 2.8183829312644493, 0.3981071705534969, 5.688529308438425, 4.265795188015916, 6.456542290346563, 2.985382618917945, 3.981071705534969, 5.888436553555884, 4.265795188015916, 3.8459178204535354, 3.890451449942805, 4.623810213992613, 2.754228703338163, 4.265795188015934, 3.1622776601683795, 7.244359600749891, 3.801893963205613, 4.365158322401657, 4.073802778041122, 3.4673685045253095, 2.089296130854028, 0.5495408738576248, 3.5481338923357457, 4.168693834703355, 0.38018939632056126, 1.6218100973589331, 2.8840315031265997, 4.477133041763614, 3.3496543915782793, 5.956621435290073, 1.678804018122559, 7.943282347242805, 2.85101826750391, 3.758374042884451, 0.10471285480508985, 2.4547089156850235, 3.491403154785848]
    medCP = [1273.503081016663, 1161.4486138403415, 1258.9254117941662, 2454.7089156850284, 988.5530946569411, 1023.2929922807537, 60255958.60743569, 794.3282347242822, 1202.2644346174106, 699.8419960022745, 851.1380382023742, 794.3282347242822, 2089.2961308540366, 933.2543007969905, 609.5368972401693, 933.2543007969905, 901.5711376059608, 912.0108393559078, 860.9937521846016, 758.5775750291851, 1023.2929922807537, 741.3102413009177, 803.526122185616, 831.7637711026691, 912.0108393559096, 1273.5030810166577, 609.5368972401693, 1047.1285480508984, 707.9457843841387, 295.1209226666384, 380189.39632056124, 676.0829753919819, 872.9713683881113, 812.8305161640995, 1174.8975549395254, 2398.83291901949, 1566.7510701081437, 1883.6490894897981, 1161.4486138403438, 1288.2495516931335, 1462.1771744567154, 1042.3174293933014]

    # Note that the x-data has been scaled to the right to cut off some of the super-metal poor outliers
    histPlot(medCN, medCP, exoXdata=medCN[:10], exoYdata=medCP[:10], linecolor='purple',
             addedScatterX=1., addedScatterY=50.,
             xxlabel="C/N", yylabel="C/P",
             xbinLeft=0, xbinRight=32.0,
             ybinLeft=0., ybinRight=2500.,
             x_bin_number=20, y_bin_number=20, redfield_ratios=True,
             saveFigure=True, figname="scatter_hist_hist/CNvsCP-direct")
