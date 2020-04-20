from django.urls import path
from django.views.generic import RedirectView

from .views import SalesPage, ServicesPage, ClientsPage, StatisticsPage

urlpatterns = [
    path('sales/', SalesPage.as_view(), name='sales'),
    path('services/', ServicesPage.as_view(), name='services'),
    path('clients/', ClientsPage.as_view(), name='clients'),
    path('statistics/', StatisticsPage.as_view(), name='statistics'),
    path('', RedirectView.as_view(url='/sales/')),
]
