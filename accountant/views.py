from django.shortcuts import render
from django.views.generic import TemplateView


class SalesPage(TemplateView):
    template_name = 'sales.html'
