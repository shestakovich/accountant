from django import forms

from accountant.models import Sale, SoldService, Client, Service


def format_timedelta(timedelta):
    minutes = timedelta.total_seconds() // 60
    return f"{minutes // 60}:{minutes % 60}"


class SaleForm(forms.ModelForm):
    client = forms.CharField(required=False)

    service_field = "service_{}"
    amount_field = "amount_{}"
    price_field = "price_{}"
    lead_time_field = "duration_{}"

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

        sold_services = SoldService.objects.filter(sale=self.instance)
        for i in (range(len(sold_services)) if not self.is_bound else range(50)):
            self.fields[self.service_field.format(i)] = forms.CharField(required=False)
            self.fields[self.amount_field.format(i)] = forms.IntegerField(min_value=1, required=False)
            self.fields[self.price_field.format(i)] = forms.DecimalField(required=False)
            self.fields[self.lead_time_field.format(i)] = forms.DurationField(required=False)

        for i, sold_service in enumerate(sold_services):
            self.initial[self.service_field.format(i)] = sold_service.service.name
            self.initial[self.amount_field.format(i)] = sold_service.amount
            self.initial[self.price_field.format(i)] = sold_service.price
            self.initial[self.lead_time_field.format(i)] = format_timedelta(sold_service.lead_time) \
                if sold_service.lead_time else ''

    def clean_client(self):
        client = self.cleaned_data.get('client')
        if client and client.split(':')[0].strip().lower() == 'id':
            try:
                pk = int(client.split(':')[1])
            except (ValueError, IndexError):
                raise forms.ValidationError('id is not int')
            try:
                client = Client.objects.get(company=self.request.user.company, pk=pk)
            except Client.DoesNotExist:
                raise forms.ValidationError('client does not exists')
        return client


    def clean(self):
        i = 0
        sold_services = []

        while self.cleaned_data.get(self.service_field.format(i)):

            sold_services.append({
                'service': self.cleaned_data.get(self.service_field.format(i)).lower(),
                'amount': self.cleaned_data.get(self.amount_field.format(i)) or 1,
                'price': self.cleaned_data.get(self.price_field.format(i)),
                'lead_time': self.cleaned_data.get(self.lead_time_field.format(i)) or None,
            })

            if not self.cleaned_data.get(self.price_field.format(i)):
                self.add_error(self.price_field.format(i), 'required')
            i += 1

        if not sold_services:
            self.add_error(self.service_field.format(0), 'required')

        self.cleaned_data['sold_services'] = sold_services

    def save(self, commit=True):
        if not commit:
            raise ValueError('In this form commit can only be True')

        sale = super().save(commit=False)
        sale.company = self.request.user.company
        sale.service_provider = self.request.user

        client = self.cleaned_data.get('client')
        if isinstance(client, Client):
            sale.client = client
        else:
            if not sale.pk or sale.client.name != client:
                if client:
                    sale.client = Client.objects.get_or_create(company=sale.company, name=client)[0]
                else:
                    sale.client = Client.objects.create(company=sale.company)

        sale.save()

        sale.services.all().delete()

        for sold_service in self.cleaned_data['sold_services']:
            sold_service['service'] = Service.objects.get_or_create(company=sale.company,
                                                                    name=sold_service['service']
                                                                    )[0]
            SoldService.objects.create(sale=sale, **sold_service)

        return sale

    class Meta:
        model = Sale
        fields = []
