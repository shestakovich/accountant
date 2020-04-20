from django.urls import path
from .views import SalesPage, ServicesPage, ClientsPage

urlpatterns = [
    path('sales/', SalesPage.as_view(), name='sales'),
    path('services/', ServicesPage.as_view(), name='services'),
    path('clients/', ClientsPage.as_view(), name='clients'),
]
