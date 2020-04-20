from django.urls import path

from api.views import service_options, client_options, service_tip

urlpatterns = [
    path('clients_options/', client_options),
    path('service_options/', service_options),
    path('service_tip/', service_tip),
]