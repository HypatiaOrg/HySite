from django.views import View
from django.http import JsonResponse\

from api.db import nea_db

def return_float_or_none(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


class PlanetView(View):
    def get(self, request):
        pl_mass_min = return_float_or_none(request.GET.get('pl_mass_min', None))
        pl_mass_max = return_float_or_none(request.GET.get('pl_mass_max', None))
        pl_radius_min = return_float_or_none(request.GET.get('pl_radius_min', None))
        pl_radius_max = return_float_or_none(request.GET.get('pl_radius_max', None))
        if any([pl_mass_min is not None, pl_mass_max is not None, pl_radius_min is not None, pl_radius_max is not None]):
            return JsonResponse(nea_db.hysite_api(pl_mass_min=pl_mass_min, pl_mass_max=pl_mass_max,
                                                  pl_radius_min=pl_radius_min, pl_radius_max=pl_radius_max), safe=False)
        else:
            return JsonResponse(nea_db.get_all_stars(), safe=False)

