from django.views import View
from api.db import hypatia_db, summary_db
from django.http import JsonResponse
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class HypatiaDataBaseView(View):
    throttle_scope = 'full_db'

    def get(self, request):
        return JsonResponse(list(hypatia_db.find_all()), safe=False)


class SummaryView(View):
    def get(self, request):
        return JsonResponse(summary_db.get_summary())
