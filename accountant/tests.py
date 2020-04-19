from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from accountant.forms import SaleForm
from accountant.models import Company, SoldService, Service, Sale, Client

User = get_user_model()


class SaleFormTests(TestCase):
    def setUp(self):
        company = Company.objects.create(name='test_company')
        self.user = User.objects.create_user(username='test_user', company=company)
        self.request = lambda x: x
        self.request.user = self.user

    def test_create_sale_service(self):
        form = SaleForm(self.request, {
            'service_0': 'test_service',
            'price_0': '123.00',
        })

        self.assertTrue(form.is_valid())

        sale = form.save()

        self.assertEqual(sale.client.name, '')
        self.assertEqual(sale.services.count(), 1)
        self.assertEqual(sale.services.all()[0].price, 123.00)
        self.assertEqual(sale.services.all()[0].service.name, 'test_service')
        self.assertEqual(sale.services.all()[0].amount, 1)
        self.assertIsNone(sale.services.all()[0].lead_time)

    def test_no_valid_create_sale(self):
        form = SaleForm(self.request, {
            'service_0': 'test_service',
            'price_0': '123.00',
            'service_1': 'fail',
        })

        self.assertFalse(form.is_valid())

        self.assertEqual(form['price_1'].errors[0], 'required')

    def test_create_sale_services(self):
        form = SaleForm(self.request, {
            'service_0': 'test_service',
            'price_0': '123.00',
            'service_1': 'test_service2',
            'amount_1': '2',
            'price_1': '2000000.00',
            'lead_time_1': '3:00:00',
        })

        self.assertTrue(form.is_valid())

        sale = form.save()

        self.assertEqual(sale.client.name, '')
        self.assertEqual(sale.services.count(), 2)
        self.assertEqual(sale.services.get(service__name='test_service2').price, 2000000.00)
        self.assertEqual(sale.services.get(service__name='test_service2').amount, 2)
        self.assertEqual(sale.services.get(service__name='test_service2').lead_time, timedelta(hours=3))

    def test_change_sale(self):
        form = SaleForm(self.request, {
            'service_0': 'test_service',
            'price_0': '123.00',
            'service_1': 'test_service2',
            'amount_1': '2',
            'price_1': '2000000.00',
            'lead_time_1': '3:00:00',
        })
        form.is_valid()
        sale = form.save()
        ins_form = SaleForm(self.request, {
            'service_0': 'test_service',
            'price_0': '123.00',
            'service_1': 'test_service_2',
            'amount_1': '2',
            'price_1': '2000000.00',
            'lead_time_1': '3:00:00',
        }, instance=sale)
        self.assertTrue(ins_form.is_valid())
        sale = ins_form.save()
        self.assertEqual(sale.services.count(), 2)
        self.assertTrue(sale.services.filter(service__name='test_service_2').exists())
        self.assertFalse(sale.services.filter(service__name='test_service2').exists())

        self.assertEqual(Client.objects.all().count(), 1)

