from django.views import View
from django.http import JsonResponse

from api.web2py.data_process import graph_query_from_request


class Graph(View):
    def get(self, request):
        data = graph_query_from_request(settings=request.GET, use_compact=True)
        if not data:
            return JsonResponse({})
        data_keys = list(data[0].keys())
        return JsonResponse(
            {data_key: data_column for data_key, data_column in
             zip(data_keys, zip(*[[data_row[key] for key in data_keys]for data_row in data]))}
        )
