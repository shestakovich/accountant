from django.db.models import Avg, Min, Prefetch, Sum, FloatField
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
            'avg_price': str(round(service.sold.aggregate(Avg('price'))['price__avg'], 2)),
            'min_price': str(round(service.sold.aggregate(Min('price'))['price__min'], 2)),
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

    clients = Client.objects.filter(company=request.user.company,
                                    purchases__services__service__name__contains=q
                                    ).distinct().order_by('-purchases__date')[:10]

    response_data = []
    for client in clients:
        purchase = client.purchases.filter(services__service__name__contains=q).prefetch_related('services__service').order_by('-date')[0]
        response_data.append({
            'name': str(client),
            'purchase_date': date_format(purchase.date, 'j E Y в H:i'),
            'purchase_services': list(purchase.services.all().values_list('service__name', flat=True)),
            'purchase_total': purchase.services.all().aggregate(total=Sum('price', output_field=FloatField()))['total'],
        })

    return JsonResponse({'clients': response_data})
