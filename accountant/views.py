from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, FloatField, Avg, Q, Case, When, ExpressionWrapper, F, Value, Count, Max
from django.db.models.functions import Cast, Extract
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView, FormView, ListView

from accountant.forms import SaleForm
from accountant.models import Sale, Service, Client


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
                'services__service').order_by('-date')
        })
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ServicesPage(LoginRequiredMixin, ListView):
    template_name = 'services.html'
    context_object_name = 'services'

    def get_queryset(self):
        queryset = Service.objects.filter(company=self.request.user.company) \
            .annotate(sum=Sum('sold__price'),
                      amount=Sum('sold__amount'),
                      avg_price=Cast('sum', FloatField()) / Cast('amount', FloatField()),
                      avg_lead_time=Avg('sold__lead_time', filter=~Q(sold__lead_time=None)),
                      profitable=Case(When(Q(avg_lead_time__isnull=False) & ~Q(avg_lead_time=timedelta(0)),
                                           then=ExpressionWrapper(
                                               F('avg_price') / Extract('avg_lead_time', 'epoch') * 60 * 60,
                                               FloatField())),
                                      default=Value(0),
                                      output_field=FloatField()
                                      )
                      ) \
            .values('name', 'sum', 'amount', 'avg_lead_time', 'avg_price', 'profitable')

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        most_popular = queryset.order_by('-amount')[0]
        most_rub_in_hour = queryset.order_by('-profitable')[0]
        most_profitable = queryset.order_by('-sum')[0]

        context = {
            'most_popular_service': most_popular,
            'most_profitable_service': most_profitable,
            'most_rub_in_hour': most_rub_in_hour,
        }
        kwargs.update(context)
        return super().get_context_data(object_list=object_list, **kwargs)


class ClientsPage(LoginRequiredMixin, ListView):
    template_name = 'clients.html'
    context_object_name = 'clients'

    def get_queryset(self):
        queryset = Client.objects. \
            filter(company=self.request.user.company) \
            .annotate(sum=Sum('purchases__services__price'),
                      amount=Count('purchases'),
                      last_purchase=Max('purchases__date')
                      ) \
            .order_by('-last_purchase')

        return queryset
