from django.views import View
from django.http import JsonResponse


from api.web2py.data_process import home_data


class Web2pyHome(View):
    def get(self, request):
        return JsonResponse(home_data, safe=False)