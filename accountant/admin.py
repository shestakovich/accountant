from django.contrib import admin

from accountant.models import Sale, Service, Company, SoldService, Client

admin.site.register(Sale)
admin.site.register(Service)
admin.site.register(Company)
admin.site.register(SoldService)
admin.site.register(Client)