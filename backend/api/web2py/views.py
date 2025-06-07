from django.views import View
from django.http import JsonResponse

from core.settings import DEBUG
from api.v2.data_process import available_catalogs_v2
from api.web2py.data_process import (home_data, units_and_fields_v2, stellar_param_types_v2,
                                     planet_param_types_v2, ranked_string_params, plot_norms,
                                     graph_settings_from_request, graph_query_pipeline_web2py, histogram_format,
                                     element_data, table_query_from_request)


class Web2pyHome(View):
    def get(self, request):
        return JsonResponse(home_data)


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
        ))


class ScatterView(View):
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        graph_settings = graph_settings_from_request(request.GET, mode='scatter')
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
        print(output_header)
        return JsonResponse({
            'labels': labels,
            'outputs': {data_key: data_column for data_key, data_column in zip(
                output_header,
                [list(i) for i in zip(*[[data_row[data_key] for data_key in graph_keys]
                                        for data_row in graph_data])],
            )},
            'star_count': star_count,
            'planet_count': planet_count,
            'is_loggable': is_loggable,
        })


class HistView(View):
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        graph_settings = graph_settings_from_request(request.GET, mode='hist')
        # get more settings about how to process the data
        graph_data, labels, _to_v2, from_v2, _is_loggable, _unique_star_names \
            = graph_query_pipeline_web2py(graph_settings=graph_settings)
        hist_all, hist_planet, edges, x_data \
            = histogram_format(graph_data=graph_data, labels=labels, from_v2=from_v2,
                               normalize_hist=graph_settings['normalize_hist'])
        return JsonResponse({
            'labels': labels,
            'hist_all': hist_all.tolist(),
            'hist_planet': hist_planet.tolist(),
            'edges': edges.tolist(),
            'x_data': x_data,
        })


class TableView(View):
    def get(self, request):
        if DEBUG:
            print(request.get_full_path())
        return JsonResponse(table_query_from_request(settings=request.GET))
