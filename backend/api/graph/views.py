from django.views import View
from django.http import JsonResponse

from api.web2py.data_process import graph_query_from_request


class Graph(View):
    def get(self, request):
        return JsonResponse(graph_query_from_request(settings=request.GET, use_compact=True), safe=False)
