from django.urls import path

from api.views import HomeView
from api.stats.views import Histogram
from api.planets.views import PlanetView
from api.web2py.views import Web2pyHome, Summary, GraphView, TableView
from api.v2.views import Nea, Data, Composition, Star, SolarNorm, AvailableElements, AvailableCatalogs


urlpatterns = [
    path('v2/nea/', Nea.as_view(), name='nea'),
    path('v2/data/', Data.as_view(), name='data'),
    path('v2/composition/', Composition.as_view(), name='composition'),
    path('v2/star/', Star.as_view(), name='solar-norm'),
    path('v2/solarnorm/', SolarNorm.as_view(), name='solar-norm'),
    path('v2/element/', AvailableElements.as_view(), name='element'),
    path('v2/catalog/', AvailableCatalogs.as_view(), name='catalog'),
    path('web2py/home/', Web2pyHome.as_view(), name='web2py-home'),
    path('web2py/summary/', Summary.as_view(), name='web2py-summary'),
    path('web2py/graph/', GraphView.as_view(), name='web2py-graph'),
    path('web2py/table/', TableView.as_view(), name='web2py-table'),
    path('planets/', PlanetView.as_view(), name='planets'),
    path('stats/histogram', Histogram.as_view(), name='histogram'),
    path('', HomeView.as_view(), name='index'),
]