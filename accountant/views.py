from datetime import timedelta, datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, FloatField, Avg, Q, Case, When, ExpressionWrapper, F, Value, Count, Max
from django.db.models.functions import Cast, Extract
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware, make_naive
from django.views.generic import TemplateView, FormView, ListView

from accountant.forms import SaleForm
from accountant.models import Sale, Service, Client, SoldService


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
        order_by = '-date'
        data = self.request.GET
        r_order_by = data.get('order_by')
        if data.get('order_by') == 'date' and not data.get('order_reverse'):
            order_by = 'date'
        elif data.get('order_by') == 'sum' and data.get('order_reverse') == 'true':
            order_by = '-sum_price'
        elif data.get('order_by') == 'sum' and not data.get('order_reverse'):
            order_by = 'sum_price'

        sales = Sale.objects\
            .filter(company=self.request.user.company)\
            .select_related('client')\
            .prefetch_related('services__service')\
            .annotate(sum_price=Sum('services__price'))\
            .order_by(order_by)

        kwargs.update({
            'sales': sales,
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
        try:
            most_popular = queryset.order_by('-amount')[0]
            most_rub_in_hour = queryset.order_by('-profitable')[0]
            most_profitable = queryset.order_by('-sum')[0]
        except IndexError:
            most_popular = None
            most_rub_in_hour = None
            most_profitable = None

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


class StatisticsPage(LoginRequiredMixin, TemplateView):
    template_name = 'statistics.html'

    def get_context_data(self, **kwargs):
        date_begin = self.request.GET.get('date_begin')
        date_end = self.request.GET.get('date_end')
        if not (date_begin and date_end):
            # TODO: Найти более адекватный способ нахождения начала дня
            time_range = [make_aware(datetime.strptime(make_naive(timezone.now()).strftime('%Y-%m-%d'), '%Y-%m-%d')),
                          make_aware(datetime.strptime(make_naive(timezone.now()).strftime('%Y-%m-%d'),
                                                       '%Y-%m-%d')) + timedelta(days=1),
                          ]
        else:
            time_range = [make_aware(datetime.strptime(date_begin, '%Y-%m-%d')),
                          make_aware(datetime.strptime(date_end, '%Y-%m-%d')),
                          ]

        q_sales_limited_time = Sale.objects.filter(date__range=time_range, company=self.request.user.company)

        earnings = q_sales_limited_time.aggregate(earnings=Sum('services__price'))['earnings']

        amount_clients = q_sales_limited_time.values('client_id').distinct().count()

        amount_new_clients = Client.objects.filter(created_date__range=time_range, company=self.request.user.company) \
            .annotate(Count('purchases')) \
            .exclude(purchases__count=0) \
            .count()

        agr_prices_lead_time = SoldService.objects.filter(sale__date__range=time_range,
                                                          sale__company=self.request.user.company) \
            .aggregate(sum_prices=Sum('price', output_field=FloatField()),
                       sum_lead_time=Sum('lead_time', filter=Q(lead_time__isnull=False)),
                       )

        avg_earnings_in_hour = agr_prices_lead_time['sum_prices'] / (
                agr_prices_lead_time['sum_lead_time'].seconds / 3600) \
            if agr_prices_lead_time['sum_lead_time'] \
            else 0

        sales = q_sales_limited_time.annotate(Sum('services__price')).order_by('-date')

        graph_points = []
        for sale in sales:
            graph_points.append({
                'x': make_naive(sale.date).strftime('%Y-%m-%dT%H:%M:%S'),
                'y': str(sale.services__price__sum),
            })

        context = {
            'avg_earnings_in_hour': round(avg_earnings_in_hour, 2),
            'total_hours': agr_prices_lead_time['sum_lead_time'],
            'earnings': earnings,
            'clients': {
                'amount': amount_clients,
                'new': amount_new_clients,
                'percent': round(amount_new_clients / amount_clients * 100, 2) if amount_clients else 0,
            },
            'graph_points': graph_points,
            'dates': {
                'day': {
                    'begin': make_naive(timezone.now()).strftime('%Y-%m-%d'),
                    'end': (make_naive(timezone.now()) + timedelta(days=1)).strftime('%Y-%m-%d'),
                },
                'month': {
                    'begin': make_naive(timezone.now()).strftime('%Y-%m-01'),
                    'end': (make_naive(timezone.now()) + timedelta(days=1)).strftime('%Y-%m-%d'),
                },
                'year': {
                    'begin': make_naive(timezone.now()).strftime('%Y-01-01'),
                    'end': (make_naive(timezone.now()) + timedelta(days=1)).strftime('%Y-%m-%d'),
                },
            }
        }
        kwargs.update(context)
        return super().get_context_data(**kwargs)
