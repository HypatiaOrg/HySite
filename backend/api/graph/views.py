from django.views import View
from django.http import JsonResponse

from api.web2py.data_process import graph_settings_from_request, graph_query_pipeline


class Graph(View):
    def get(self, request):
        graph_settings = graph_settings_from_request(request.GET)
        graph_data = graph_query_pipeline(graph_settings=graph_settings)
        if not graph_data:
            return JsonResponse({})
        data_keys = list(graph_data[0].keys())
        return JsonResponse(
            {data_key: data_column for data_key, data_column in
             zip(data_keys, zip(*[[data_row[key] for key in data_keys]for data_row in graph_data]))}
        )
