import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from accountant.models import Company, Sale, Client, SoldService, Service

User = get_user_model()


class ServiceTipTests(TestCase):
    def setUp(self):
        company = Company.objects.create(name='test_company')
        self.client.force_login(User.objects.create_user(
            username='test_user',
            company=company
        ))
        sale = Sale.objects.create(
            client=Client.objects.create(company=company, name='test_client'),
            company=company,
        )
        SoldService.objects.create(
            sale=sale,
            service=Service.objects.create(company=company,
                                           name='test_service'
                                           ),
            price=200.0,
            lead_time=timedelta(hours=2),
        )

    def test_load_tip(self):
        response = self.client.get('/api/service_tip/', {'q': 'test_service'})
        rjson = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(rjson.get('error'))
        self.assertEqual(rjson['title'], 'Test_service')


class ClientOptions(TestCase):
    def setUp(self):
        company = Company.objects.create(name='test_company')
        self.client.force_login(User.objects.create_user(
            username='test_user',
            company=company
        ))
        sale = Sale.objects.create(
            client=Client.objects.create(company=company, name='test_client'),
            company=company,
        )
        sale2 = Sale.objects.create(
            client=Client.objects.create(company=company, name='test_client2'),
            company=company,
        )
        SoldService.objects.create(
            sale=sale,
            service=Service.objects.create(company=company,
                                           name='test_service'
                                           ),
            price=200.0,
            lead_time=timedelta(hours=2),
        )

        SoldService.objects.create(
                    sale=sale,
                    service=Service.objects.create(company=company,
                                                   name='test_service2'
                                                   ),
                    price=100.0,
                )
        SoldService.objects.create(
                    sale=sale2,
                    service=Service.objects.create(company=company,
                                                   name='test_service3'
                                                   ),
                    price=100.0,
                )

    def test_load_options(self):
        response = json.loads(self.client.get('/api/clients_options/', {'q': 'test_c'}).content)
        self.assertEqual(response['clients'][0]['name'], 'test_client2')

    def test_load_options_by_service(self):
        response = self.client.get('/api/client_options_by_service/', {'q': 'tes'})
        self.assertEqual(response.status_code, 200)
        r_json = json.loads(response.content)
        self.assertEqual(r_json['clients'][1]['name'], 'test_client2')
        self.assertEqual(r_json['clients'][1]['purchase_total'], 100.0)
        self.assertEqual(len(r_json['clients']), 2)

