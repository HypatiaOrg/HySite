from django.views import View
from django.http import JsonResponse, StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from core.settings import DEBUG
from api.v2.data_process import available_catalogs_v2, representative_error
from api.web2py.table import table_from_request, table_download_lines, DOWNLOAD_FORMATS
from api.web2py.settings import settings_schema
from api.web2py.plots import axes_from_settings, group_targets, requested_target_handles, histogram_series
from api.web2py.density import density_data, marginal_bins, valid_points
from api.web2py.data_process import (home_data, units_and_fields_v2, stellar_param_types_v2, is_true_str,
                                     planet_param_types_v2, ranked_string_params, plot_norms,
                                     graph_settings_from_request, graph_query_pipeline_web2py, histogram_format,
                                     element_data, table_query_from_request, targets_metadata,
                                     )


class Web2pyHome(View):
    def get(self, request):
        return JsonResponse(home_data)


class Settings(View):
    """The frontend's settings model: names, defaults, kinds and choices (api.web2py.settings)."""
    def get(self, request):
        return JsonResponse(settings_schema())


class Summary(View):
    def get(self, request):
        return JsonResponse(dict(
            units_and_fields=units_and_fields_v2,
            stellar_param_types=stellar_param_types_v2,
            planet_param_types=planet_param_types_v2,
            ranked_string_params=ranked_string_params,
            catalogs=available_catalogs_v2,
            solarnorms=plot_norms,
            element_data=element_data,
            representative_error=representative_error,
            targets=targets_metadata,
        ))


def get_graph_data(settings, return_targets: bool = False):
    """The scatter data for the frontend's settings (a request's GET, or a copy of it)."""
    graph_settings = graph_settings_from_request(settings, mode='scatter')
    graph_settings['return_targets'] = return_targets
    # get more settings about how to process the data
    graph_data, labels, _to_v2, from_v2, is_loggable, unique_star_names \
        = graph_query_pipeline_web2py(graph_settings=graph_settings)
    axis_mapping = graph_settings['axis_mapping']
    output_header = ['name'] + [f'{x_axis}axis' for x_axis in axis_mapping.keys()]
    graph_keys = [from_v2[column_name] if column_name in from_v2.keys() else column_name
                  for column_name in output_header]
    if any([
        graph_settings['planet_params_returned'],
        graph_settings['planet_params_match_filters'],
        graph_settings['planet_params_value_filters'],
    ]):
        star_count = len(unique_star_names)
        planet_count = len(graph_data)
    else:
        star_count = len(graph_data)
        planet_count = None
    return_data = {
        'labels': labels,
        'outputs': {data_key: data_column for data_key, data_column in zip(
            output_header,
            [list(i) for i in zip(*[[data_row[data_key] for data_key in graph_keys]
                                    for data_row in graph_data])],
        )},
        'star_count': star_count,
        'planet_count': planet_count,
        'is_loggable': is_loggable,
        # the axis decisions the settings imply (api.web2py.plots)
        'axes': axes_from_settings(settings, labels, is_loggable),
    }
    # the bins of the optional histograms along the axes (api.web2py.density), from the points with both values
    _names, x_values, y_values = valid_points(return_data['outputs'])
    return_data['bins'] = marginal_bins(x_values, y_values, axis_mapping, settings)
    if return_targets:
        return_data['targets'] = [data_row['target_handles'] for data_row in graph_data]
        outputs = return_data['outputs']
        layers, number_of_targets = group_targets(
            names=outputs.get('name', []), xaxis=outputs.get('xaxis', []), yaxis=outputs.get('yaxis', []),
            target_handles=return_data['targets'], requested_handles=requested_target_handles(settings),
            show_all=is_true_str(settings.get('show_all', 'false')),
            or_logic=is_true_str(settings.get('or_logic', 'false')))
        return_data['layers'] = layers
        return_data['number_of_targets'] = number_of_targets
    return return_data


class ScatterView(View):
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        return JsonResponse(get_graph_data(request.GET))


class TargetsView(View):
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        return JsonResponse(get_graph_data(request.GET, return_targets=True))


class DensityView(View):
    """The density page's data: the scatter points with the bins, range, colours and axes decided (api.web2py.density)."""
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        # the density map has two axes: a z axis the scatter page left in the session must not restrict the stars.
        # Its axes are never logarithmic: the bins are in data units, and the page has no log toggles (issue #35)
        settings = request.GET.copy()
        settings['zaxis1'] = 'none'
        settings['xaxislog'] = 'false'
        settings['yaxislog'] = 'false'
        graph_settings = graph_settings_from_request(settings, mode='scatter')
        return JsonResponse(density_data(graph_data=get_graph_data(settings),
                                         axis_mapping=graph_settings['axis_mapping'], settings=settings))


class HistView(View):
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        graph_settings = graph_settings_from_request(request.GET, mode='hist')
        # get more settings about how to process the data
        graph_data, labels, _to_v2, from_v2, _is_loggable, _unique_star_names \
            = graph_query_pipeline_web2py(graph_settings=graph_settings)
        # the histogram as named series (api.web2py.plots); hist_all/hist_planet/edges/x_data as before
        histogram = histogram_series(graph_data=graph_data, labels=labels, from_v2=from_v2,
                                     normalize=graph_settings['normalize_hist'])
        return JsonResponse({'labels': labels, **histogram})


@method_decorator(csrf_exempt, name='dispatch')
class TableView(View):
    """
    The table data. With 'tablecols' in the request: the frontend's table, built here (api.web2py.table),
    as JSON or as a csv/tsv/psv download ('format'). Without it: the older column-wise data, kept for
    existing clients. POST takes the same settings as a form body, for long star lists.
    """
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        return self.table(request.GET)

    def post(self, request):
        return self.table(request.POST)

    @staticmethod
    def table(settings):
        if 'tablecols' not in settings:
            return JsonResponse(table_query_from_request(settings=settings))
        file_format = str(settings.get('format', 'json')).lower()
        if file_format in DOWNLOAD_FORMATS:
            settings = settings.copy()
            settings['download'] = 'true'
            table = table_from_request(settings)
            response = StreamingHttpResponse(table_download_lines(table, file_format),
                                             content_type=f'text/{file_format}; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="hypatia.{file_format}"'
            return response
        return JsonResponse(table_from_request(settings))
