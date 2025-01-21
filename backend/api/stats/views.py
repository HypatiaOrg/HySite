from django.views import View
from django.http import JsonResponse
from api.db import hypatia_db


class Histogram(View):
    def get(self, request):
        return JsonResponse(hypatia_db.get_abundance_count(norm_key='absolute', by_element=True, count_stars=True), safe=False)
