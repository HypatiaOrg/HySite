from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path('v2/solarnorm/', views.SolarNorm.as_view(), name='solar-norm'),
    path('v2/', views.api_v2, name='api-v2'),
    path('v1/', views.api_v1, name='api-v1'),  # V1 is the same as V2 since before the migration from Web2py
    path('', views.HomeView.as_view(), name='index'),
]