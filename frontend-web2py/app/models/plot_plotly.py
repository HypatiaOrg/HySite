import math, statistics, numpy as np, plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, sys

def create_hypatia_plot(xaxis1="N", xaxis2="H", yaxis1="Na", yaxis2="N",
                        mode="both", width_override=None) -> str:
    from hypatia.tools.web_query import get_graph_data
    from hypatia.configs.file_paths import plot_dir
    sys.path.append(os.path.dirname(__file__))

    colors = [
        [0.0, '#4e11b7'],
        [0.2, '#6c5ce7'],
        [0.4, '#dfe6e9'],
        [0.6, '#81ecec'],
        [0.8, '#92F7B0'],
        [0.9, '#F7C492'],
        [1.0, '#d63031']
    ]

    element_err = {
        "Ag": 0.4,
        "Al": 0.12,
        "Al_II": 0.3,
        "Au": 0.6,
        "Ba": 0.3,
        "Ba_II": 0.38,
        "Be": 0.24,
        "Be_II": 0.1,
        "C": 0.18,
        "Ca": 0.12,
        "Ca_II": 0.06,
        "Cd": 0.5,
        "Ce": 0.152,
        "Ce_II": 0.14,
        "Cl": 0.46,
        "Co": 0.08,
        "Co_II": 0.1,
        "Cr": 0.09,
        "Cr_II": 0.132,
        "Cu": 0.16,
        "Cu_II": 0.46,
        "Dy": 0.8,
        "Dy_II": 0.22,
        "Er": 0.4,
        "Er_II": 0.32,
        "Eu": 0.22,
        "Eu_II": 0.2,
        "F": 0.24,
        "Fe": 0.08,
        "Ga": 0.4,
        "Ga_II": 0.38,
        "Gd": 1.2,
        "Gd_II": 0.26,
        "Hf": 0.4,
        "Hf_II": 0.36,
        "Hg_II": 0.36,
        "Ho_II": 0.42,
        "In_II": 0.4,
        "Ir": 0.56,
        "K": 0.08,
        "La": 0.172,
        "La_II": 0.44,
        "Li": 0.2,
        "Lu_II": 0.3,
        "Mg": 0.14,
        "Mn": 0.112,
        "Mn_II": 0.112,
        "Mo": 0.24,
        "Mo_II": 0.4,
        "N": 0.22,
        "Na": 0.08,
        "Nb": 0.52,
        "Nb_II": 0.3,
        "Nd": 0.14,
        "Nd_II": 0.14,
        "Ni": 0.1,
        "Ni_II": 0.16,
        "O": 0.18,
        "Os": 0.22,
        "P": 0.08,
        "Pb": 0.44,
        "Pb_II": 0.44,
        "Pd": 0.38,
        "Pr": 0.26,
        "Pr_II": 0.2,
        "Pt": 0.3,
        "Rb": 0.24,
        "Re_II": 0.3,
        "Rh": 0.44,
        "Ru": 0.24,
        "Ru_II": 0.34,
        "S": 0.18,
        "Sb": 0.34,
        "Sc": 0.1,
        "Sc_II": 0.18,
        "Se": 0.5,
        "Si": 0.1,
        "Si_II": 0.1,
        "Sm": 0.14,
        "Sm_II": 0.31,
        "Sn": 0.44,
        "Sr": 0.212,
        "Sr_II": 0.3,
        "Tb_II": 0.22,
        "Tc": 0.2,
        "Te": 0.54,
        "Th": 0.08,
        "Th_II": 0.28,
        "Ti": 0.1,
        "Ti_II": 0.12,
        "Tm_II": 0.4,
        "V": 0.14,
        "V_II": 0.21,
        "W": 0.68,
        "W_II": 0.2,
        "Y": 0.17,
        "Y_II": 0.16,
        "Yb_II": 0.28,
        "Zn": 0.152,
        "Zn_II": 0.62,
        "Zr": 0.2,
        "Zr_II": 0.16
    }

    hypatia_colormap = colors

    # same setup logic you already have:
    if xaxis1 == "H":
        width_x = element_err[xaxis2]
    elif xaxis2 == "H":
        width_x = element_err[xaxis1]
    else:
        width_x = math.sqrt((element_err[xaxis1])**2 + (element_err[xaxis2])**2)

    if yaxis1 == "H":
        width_y = element_err[yaxis2]
    elif yaxis2 == "H":
        width_y = element_err[yaxis1]
    else:
        width_y = math.sqrt((element_err[yaxis1])**2 + (element_err[yaxis2])**2)

    plot_data = get_graph_data(xaxis1=xaxis1, xaxis2=xaxis2, yaxis1=yaxis1, yaxis2=yaxis2)
    if plot_data is None:
        return "<p>No data available.</p>"

    x_handle = f"{xaxis1}_{xaxis2}"
    y_handle = f"{yaxis1}_{yaxis2}"
    x = plot_data[x_handle]
    y = plot_data[y_handle]

    # Choose plot mode
    if mode == "hist":
        fig = go.Figure(go.Histogram(x=x, marker_color="#4e11b7"))
        fig.update_layout(title="Histogram", xaxis_title=f"[{xaxis1}/{xaxis2}]", yaxis_title="Frequency")

    elif mode == "heat":
        fig = go.Figure(go.Histogram2d(x=x, y=y, colorscale=hypatia_colormap))
        fig.update_layout(title="Heatmap", xaxis_title=f"[{xaxis1}/{xaxis2}]", yaxis_title=f"[{yaxis1}/{yaxis2}]")

    else:  # both
        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.8, 0.2],
            row_heights=[0.2, 0.8],
            shared_xaxes=True,
            shared_yaxes=True,
            specs=[[{"type": "histogram"}, None],
                   [{"type": "histogram2d"}, {"type": "histogram"}]]
        )
        fig.add_trace(go.Histogram(x=x, marker_color="#4e11b7"), row=1, col=1)
        fig.add_trace(go.Histogram(y=y, marker_color="#4e11b7"), row=2, col=2)
        fig.add_trace(go.Histogram2d(x=x, y=y, colorscale=hypatia_colormap), row=2, col=1)
        fig.update_layout(title="Heatmap with Marginal Histograms")

    # Convert figure to HTML
    html_str = fig.to_html(include_plotlyjs="cdn", full_html=True)
    return html_str


if __name__ == "__main__":
    html_out = create_hypatia_plot("Fe", "H", "Si", "H", mode="both")
    with open("hypatia_plot.html", "w") as f:
        f.write(html_out)


