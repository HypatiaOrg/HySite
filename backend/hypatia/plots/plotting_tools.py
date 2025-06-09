import math
import numpy as np

from hypatia.plots.scatter_hist_hist_plot import histPlot

'''
Copied over from standard_library on 6 June, 2025. Since the major update Dec 2024, some of these definitions
do not work and will need to be updated.
'''

def element_plot(output_star_data, divide_by: str = "Fe", numerators: list[str] = None):
    #Currently not working because output_star_data.star_names doesn't match the actual starname objects
    if numerators is None:
        numerators = ["Si", "Fe", "Mg"]
    element_list = numerators[:]
    numerators.remove(divide_by)
    star_names_list = list(sorted(output_star_data.star_names))
    dict_to_element_array = {}
    for element in element_list:
        dict_to_element_array[element] = np.array([output_star_data.__getattribute__(star_name)
                                                  .reduced.__getattribute(element).median
                                                   for star_name in star_names_list])
    division_arrays = [dict_to_element_array[numerator] - dict_to_element_array[divide_by]
                       for numerator in numerators]
    histPlot(xdata=division_arrays[0], ydata=division_arrays[1],
             xxlabel="[" + numerators[0] + "/" + divide_by + "]", yylabel="[" + numerators[1] + "/" + divide_by + "]",
             saveFigure=True)


def make_element_distance_plots(from_scratch=False):
    nat_cat = NatCat(catalogs_from_scratch=from_scratch, verbose=True,
                     get_abundance_data=True, get_exo_data=True, refresh_exo_data=False)
    nat_cat.star_data.get_element_ratio_and_distance(element_set=None,
                                                     distance_list=[0.0, 30.0, 60.0, 90.0, 150.0, 500.0],
                                                     xlimits_list=None, ylimits_list=None, has_exoplanet=None,
                                                     use_median=True)
    return nat_cat


def plot_all(xaxis):
    """
    :param xaxis: The elements will be plotted on the y-axis, this allows you to specify the x-axis
    :return: plots saved to /xy_plot
    """
    elems = list(sorted(stats.star_count_per_element.available_bins, key=element_rank))
    for elem in elems:
        output_star_data.xy_plot(x_thing=xaxis, y_thing=elem, color="darkorchid", show=False, save=True)


def calc_molar_fractions(elemlist, solarvals, errvals, **kwargs):
    """

       histPlot(molarX, molarY, exoXdata=exo_molarX, exoYdata=exo_molarY, linecolor='purple',
             addedScatterX=1., addedScatterY=50.,
             xxlabel=Xnum+"/"+Xdenom, yylabel=Ynum+"/"+Ydenom,
             xbinLeft=0, xbinRight=32.0,
             ybinLeft=0., ybinRight=2500.,
             x_bin_number=20, y_bin_number=20, redfield_ratios=True,
             saveFigure=True, figname="scatter_hist_hist/"+Xnum+Xdenom+"vs"+Ynum+Ydenom)

    Could run this on the output created from picklemyself, without having to reload or copy and paste
    """
    Xnum, Xdenom, Ynum, Ydenom = elemlist
    Xnum_sol, Xdenom_sol, Ynum_sol, Ydenom_sol = solarvals
    Xnum_err, Xdenom_err, Ynum_err, Ydenom_err = errvals
    star_names_list = list(sorted(output_star_data.star_names))
    med_elem_dict = {single_element: [] for single_element in set(elemlist)}
    exo_med_elem_dict = {single_element: [] for single_element in set(elemlist)}
    for star_name in star_names_list:
        single_star = output_star_data.__getattribute__(star_name)
        if set(elemlist).issubset(single_star.reduced_abundances.available_abundances):
            for workingelem in set(elemlist):
                if "exo" in single_star.available_data_types:
                    exo_median = single_star.reduced_abundances.__getattribute__(workingelem).median
                    exo_med_elem_dict[workingelem].append(exo_median)
                else:
                    median = single_star.reduced_abundances.__getattribute__(workingelem).median
                    med_elem_dict[workingelem].append(median)

    molarX = [10 ** (med_elem_dict[Xnum][kk] + Xnum_sol - (med_elem_dict[Xdenom][kk] + Xdenom_sol)) for kk in
              range(len(med_elem_dict[Xnum]))]
    molarY = [10 ** (med_elem_dict[Ynum][kk] + Ynum_sol - (med_elem_dict[Ydenom][kk] + Ydenom_sol)) for kk in
              range(len(med_elem_dict[Ynum]))]

    XnumXdenomerr = (10 ** (math.sqrt(Xnum_err ** 2 + Xdenom_err ** 2)) - 1.) * np.median(molarX)
    YnumYdenomerr = (10 ** (math.sqrt(Ynum_err ** 2 + Ydenom_err ** 2)) - 1.) * np.median(molarY)

    exo_molarX = [10 ** (exo_med_elem_dict[Xnum][kk] + Xnum_sol - (exo_med_elem_dict[Xdenom][kk] + Xdenom_sol)) for kk
                  in
                  range(len(exo_med_elem_dict[Xnum]))]
    exo_molarY = [10 ** (exo_med_elem_dict[Ynum][kk] + Ynum_sol - (exo_med_elem_dict[Ydenom][kk] + Ydenom_sol)) for kk
                  in range(len(exo_med_elem_dict[Ynum]))]

    print("Total number of stars is", len(molarX) + len(exo_molarX), "where", len(exo_molarX),
          "are exoplanet host stars")

    histPlot(molarX, molarY, exoXdata=exo_molarX, exoYdata=exo_molarY, xerror=XnumXdenomerr, yerror=YnumYdenomerr,
             linecolor=kwargs["linecolor"],
             addedScatterX=kwargs["addedScatterX"], addedScatterY=kwargs["addedScatterY"],
             xbinLeft=kwargs["xbinLeft"], xbinRight=kwargs["xbinRight"],
             ybinLeft=kwargs["ybinLeft"], ybinRight=kwargs["ybinRight"],
             x_bin_number=kwargs["x_bin_number"], y_bin_number=kwargs["y_bin_number"],
             redfield_ratios=kwargs["redfield_ratios"], saveFigure=kwargs["saveFigure"], do_pdf=kwargs["do_pdf"],
             xxlabel=Xnum + "/" + Xdenom, yylabel=Ynum + "/" + Ydenom,
             figname="scatter_hist_hist/" + Xnum + Xdenom + "vs" + Ynum + Ydenom)
