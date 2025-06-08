import plotly.express as px

def create_plotly_scatter(name: list[str],
                          xaxis: list[str | float | int], yaxis: list[str | float | int], zaxis: list[str | float | int],
                          x_label: str = None, y_label: str = None, z_label: str = None,
                          star_count: int = None, planet_count: int = None,
                          do_xlog: bool = False, do_ylog: bool = False, do_zlog: bool = False,
                          xaxisinv: bool = False, yaxisinv: bool = False, zaxisinv: bool = False,
                          has_zaxis: bool = False, do_gridlines: bool = False,):
    # Create a scatter plot
    fig = px.scatter(x=xaxis, y=yaxis)
    # Convert the figure to HTML
    return fig.to_html(include_plotlyjs=True)
