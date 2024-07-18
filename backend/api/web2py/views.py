from django.views import View
from django.http import JsonResponse


from api.v2.data_process import available_catalogs_v2
from api.web2py.data_process import (home_data, units_and_fields_v2, stellar_param_types_v2,
                                     planet_param_types_v2, ranked_string_params, plot_norms,
                                     element_data, graph_query_from_request)


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


class GraphView(View):
    def get(self, request):
        dict(request.GET)
        return JsonResponse(graph_query_from_request(settings=request.GET))
