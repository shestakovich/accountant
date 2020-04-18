from django.urls import path
from .views import SalesPage

urlpatterns = [
    path('', SalesPage.as_view(), name='sales'),
]
