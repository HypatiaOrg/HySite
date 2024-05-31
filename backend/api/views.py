import datetime
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView
from django.views import View
from .mongo import normalizations_v2


class HomeView(TemplateView):
    template_name = 'index.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


def api_v1(request):
    """ Parse the request and redirect to the v2 API """
    if request.path:
        new_path = request.path.replace("/api/v1/", "/api/v2/")
        return HttpResponseRedirect(new_path)

    return HttpResponse("No path found in request", status=400)


def api_v2(request):
    now = datetime.datetime.now()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)


class SolarNorm(View):
    def get(self, request):
        # <view logic>
        return JsonResponse(normalizations_v2, safe=False)

