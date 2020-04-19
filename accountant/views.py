from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView, FormView

from accountant.forms import SaleForm
from accountant.models import Sale


class SalesPage(LoginRequiredMixin, FormView):
    template_name = 'sales.html'
    form_class = SaleForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        kwargs.update({
            'sales': Sale.objects.filter(company=self.request.user.company).select_related('client').prefetch_related(
                'services__service')
        })
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
