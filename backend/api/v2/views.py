from django.views import View
from django.http import JsonResponse, HttpResponse

from api.web2py.data_process import (graph_settings_from_request, graph_query_pipeline_web2py,
                                     histogram_format)
from api.v2.data_process import (normalizations_v2, available_elements_v2, available_catalogs_v2, get_star_data_v2,
                                 get_abundance_data_v2, element_parse_v2, get_norm_key, max_unique_star_names, nea_v2,
                                 get_norm_data)


class SolarNorm(View):
    def get(self, request):
        return JsonResponse(normalizations_v2, safe=False)


class AvailableElements(View):
    def get(self, request):
        return JsonResponse(available_elements_v2, safe=False)


class AvailableCatalogs(View):
    def get(self, request):
        return JsonResponse(available_catalogs_v2, safe=False)


class Star(View):
    def get(self, request):
        query_dict_names = request.GET.getlist('name', None)
        if query_dict_names:
            names_queried = query_dict_names
        else:
            names_queried = list(request.GET.keys())
        # remove any spaces in the names to match the database format
        return JsonResponse(list(get_star_data_v2(star_names=names_queried)), safe=False)


class Composition(View):
    def get(self, request):
        star_names_list = request.GET.getlist('name', None)
        elements_list = request.GET.getlist('element', None)
        solar_norms_list = request.GET.getlist('solarnorm', None)
        if not all([star_names_list, elements_list]):
            return HttpResponse(
                'Invalid query parameters, expected three arrays (lists) of the same length named "name", "element", and "solarnorm" ',
                status=400)
        if not solar_norms_list:
            solar_norms_list = ['lodders09'] * len(star_names_list)
        # The Legacy API required three equal length lists of star names, elements, and solar normalizations.
        elif not (len(star_names_list) == len(elements_list) == len(solar_norms_list)):
            return HttpResponse(
                f'Invalid query parameters, expected three arrays (lists) of the same length named "name", "element", '
                f'and "solarnorm" got lengths {len(star_names_list)}, {len(elements_list)}, '
                f'and {len(solar_norms_list)}',
                status=400)
        # since repeated values in the query are allowed, we need to make sure we only query unique values
        star_names_db_unique = set()
        element_ids_unique = set()
        solar_norms_unique = set()
        request_to_database_format = {}
        for star_name, element_str, solar_norm in zip(star_names_list, elements_list, solar_norms_list):
            # the star names checking is done later using database strategies
            star_name_db_format = star_name.replace(' ', '').lower()
            star_names_db_unique.add(star_name_db_format)
            # element names are parsed for the database and checked for validity
            element_id = element_parse_v2(element_str)
            if element_id is None:
                return HttpResponse(
                    f'Failed to parse the received element: {element_str}, '
                    f'the parsing result was {element_id}', status=400)
            element_ids_unique.add(element_id)
            # solar norms are minimally parsed and checked for validity
            solarnorm_id = get_norm_key(solar_norm)
            if solarnorm_id is None:
                return HttpResponse(
                    f'Failed to parse the received solar norm: {solar_norm}, '
                    f'the parsing result was {solarnorm_id}', status=400)
            solar_norms_unique.add(solarnorm_id)
            # These three parts of information will be used to map the database results to the user's requested list
            user_request_id = (star_name, element_str, solar_norm)
            db_result_id = (star_name_db_format, element_id, solarnorm_id)
            request_to_database_format[user_request_id] = db_result_id
        if max_unique_star_names < len(star_names_db_unique):
            return HttpResponse(
                f'Invalid query parameters, expected less than {max_unique_star_names} unique star names, got {len(star_names_list)}',
                status=400)
        # order the results in the order the user requested
        user_packaged_results = get_abundance_data_v2(
            star_names_db_unique=star_names_db_unique,
            element_ids_unique=element_ids_unique,
            solar_norms_unique=solar_norms_unique,
        )
        return JsonResponse([user_packaged_results[db_result_id] | {'requested_name': user_star_name,
                                                                    'requested_element': user_element_str,
                                                                    'requested_solarnorm': user_solar_norm}
                             for (user_star_name, user_element_str, user_solar_norm), db_result_id
                             in request_to_database_format.items()],
                            safe=False)


class Data(View):
    def get(self, request):
        graph_settings = graph_settings_from_request(request.GET)
        # get more settings about how to process the data
        graph_data, labels, to_v2, from_v2, _is_loggable, _unique_star_names \
            = graph_query_pipeline_web2py(graph_settings=graph_settings)

        if graph_settings['is_histogram']:
            hist_all, hist_planet, edges, x_data \
                = histogram_format(graph_data=graph_data, labels=labels, from_v2=from_v2,
                                   normalize_hist=graph_settings['normalize_hist'])
            return JsonResponse({
                'count': len(x_data),
                'labels': labels,
                'all_hypatia': hist_all.tolist(),
                'exo_hosts': hist_planet.tolist(),
                'edges': edges.tolist(),
            })
        else:
            return JsonResponse({
                'counts': len(graph_data),
                'labels': labels,
                'solarnorm': get_norm_data(graph_settings['solarnorm_id']),
                'values': [
                    {to_v2[key] if key in to_v2.keys() else key: value for key, value in db_return.items()}
                    for db_return in graph_data
                ],
            })


class Nea(View):
    def get(self, request):
        return JsonResponse(nea_v2(), safe=False)