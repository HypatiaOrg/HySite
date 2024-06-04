from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from .mongo import normalizations_v2, available_elements_v2, available_catalogs_v2


class HomeView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class SolarNorm(View):
    def get(self, request):
        return JsonResponse(normalizations_v2, safe=False)


class AvailableElements(View):
    def get(self, request):
        return JsonResponse(available_elements_v2, safe=False)


class AvailableCatalogs(View):
    def get(self, request):
        return JsonResponse(available_catalogs_v2, safe=False)