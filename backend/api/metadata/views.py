from django.views import View
from api.db import summary_doc
from django.http import JsonResponse


class SolarNorms(View):
    def get(self, request):
        return JsonResponse(summary_doc['normalizations'], safe=False)


class RepresentativeErrorView(View):
    def get(self, request):
        return JsonResponse(summary_doc['representative_error'], safe=False)
