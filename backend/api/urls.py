from django.urls import path

from api.views import HomeView
from api.web2py.views import Web2pyHome
from api.v2.views import Data, Composition, Star, SolarNorm, AvailableElements, AvailableCatalogs

urlpatterns = [
    path('v2/Data/', Data.as_view(), name='data'),
    path('v2/composition/', Composition.as_view(), name='composition'),
    path('v2/star/', Star.as_view(), name='solar-norm'),
    path('v2/solarnorm/', SolarNorm.as_view(), name='solar-norm'),
    path('v2/element/', AvailableElements.as_view(), name='element'),
    path('v2/catalog/', AvailableCatalogs.as_view(), name='catalog'),
    path('web2py/home/', Web2pyHome.as_view(), name='web2py-home'),
    path('', HomeView.as_view(), name='index'),
]