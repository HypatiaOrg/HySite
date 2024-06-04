from django.urls import path

from . import views

urlpatterns = [
    path('v2/star/', views.Star.as_view(), name='solar-norm'),
    path('v2/solarnorm/', views.SolarNorm.as_view(), name='solar-norm'),
    path('v2/element/', views.AvailableElements.as_view(), name='element'),
    path('v2/catalog/', views.AvailableCatalogs.as_view(), name='catalog'),
    path('', views.HomeView.as_view(), name='index'),
]