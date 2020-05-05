from django.db.models import Avg, Min, Prefetch, Sum, FloatField, F
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.formats import date_format
from django.utils.timezone import make_naive

from accountant.models import Service, Sale, SoldService, Client


def login_required(f):
    def new_f(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'login_required'})
        return f(request, *args, **kwargs)
    return new_f


@login_required
def service_options(request):
    q = request.GET.get('q')
    services = [{'main': el.capitalize()} for el in
                Service.objects.filter(company=request.user.company,
                                       name__contains=q.strip().lower()
                                       ).values_list('name', flat=True)]

    return JsonResponse({'services': services})


@login_required
def service_tip(request):
    q = request.GET.get('q')
    try:
        service = Service.objects.get(company=request.user.company, name=q.strip().lower())
    except Service.DoesNotExist:
        return JsonResponse({'error': 'does not exists'})
    else:
        response = {
            'title': service.name.capitalize(),
            'avg_price': str(round(service.sold
                                   .annotate(price_for_one=Cast('price', FloatField())/Cast('amount', FloatField()))
                                   .aggregate(avg_price=Avg('price_for_one'))['avg_price'], 2)),
            'min_price': str(round(service.sold
                                   .annotate(price_for_one=Cast('price', FloatField())/Cast('amount', FloatField()))
                                   .aggregate(avg_price=Min('price_for_one'))['avg_price'], 2)),
            'chart_data': [],
        }
        for sold_service in service.sold.select_related('sale').order_by('sale__date'):
            response['chart_data'].append({'x': make_naive(sold_service.sale.date).strftime('%Y-%m-%dT%H:%M:%S'),
                                           'y': str(sold_service.price)})
        return JsonResponse(response)


@login_required
def client_options(request):
    q = request.GET.get('q')
    if not q:
        return JsonResponse({'error': 'not q'})
    q = q.lower().strip()

    purchases = Sale.objects \
        .filter(company=request.user.company) \
        .prefetch_related(Prefetch('services', queryset=SoldService.objects.select_related('service'))) \
        .annotate(total=Sum('services__price')) \
        .order_by('-date')

    clients = Client.objects.filter(company=request.user.company,
                                    name__icontains=q,
                                    )\
        .prefetch_related(Prefetch('purchases', queryset=purchases))\
        .order_by('-purchases__date')

    res = [
        {
            'name': client.name,
            'date_last_purchase': client.purchases.all()[0].date,
            'services_list_last_purchase': list(client.purchases.all()[0].services.values_list('service__name', flat=True)),
            'total_last_purchase': client.purchases.all()[0].total,
        }
        for client in clients
    ]

    return JsonResponse({'clients': res})


@login_required
def client_options_by_service(request):
    q = request.GET.get('q')
    if not q:
        return JsonResponse({'error': 'not q'})
    q = q.lower().strip()

    clients = Client.objects.raw('''
        select distinct on (1) client.id,
                           client.name,
                           sale.date as sale_date,
                           sale.id as sale_id,
                           sum(sold_s.price) over (partition by sale.id) as sale_total
        from accountant_client as client
                 join accountant_sale as sale on client.id = sale.client_id
                 join accountant_soldservice as sold_s on sale.id = sold_s.sale_id
                 join accountant_service as service on sold_s.service_id = service.id
        where service.name like %(q)s
        and client.company_id=%(company)s
        order by 1, sale_date desc
    ''', {'q': f'%{q}%', 'company': request.user.company.id})


    sales = Sale.objects.filter(id__in=[client.sale_id for client in clients]).prefetch_related('services__service').order_by('-date')

    response_data = []

    for client, sale in zip(clients, sales):
        response_data.append({
            'name': str(client),
            'purchase_date': date_format(client.sale_date, 'j E Y в H:i'),
            'purchase_services': list(sale.services.all().values_list('service__name', flat=True)),
            'purchase_total': float(client.sale_total),
        })

    return JsonResponse({'clients': response_data})
