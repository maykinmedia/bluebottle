import json
from mock import patch
from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status
from bluebottle.orders.models import Order
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.utils.model_dispatcher import get_order_model
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory, OrderActionFactory
from bluebottle.bb_orders.views import ManageOrderDetail
from bluebottle.payments_mock.adapters import MockPaymentAdapter

class TestOrderPaymentPermissions(TestCase):
    """ Test the permissions for order ownership in bb_orders """

    def setUp(self):
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.order = OrderFactory.create(user=self.user1, total=10)

        self.order_payment_data = {
            'order': self.order.id,
            'integration_data': {'issuerId': 'huey'},
            'payment_method': 'mockIdeal',
            'meta_data': None,
            'user': None,
            'status': '',
            'updated': None,
            'amount' : 25

        }

    @patch.object(MockPaymentAdapter, 'create_payment')
    def test_create_orderpayment_user_owner(self, mock_create_payment):
        """ User that is owner of the order tries to create an order payment gets a 201 CREATED"""

        response = self.client.post(reverse('manage-order-payment-list'), self.order_payment_data,
                                   HTTP_AUTHORIZATION=self.user1_token)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_orderpayment_user_not_owner(self):
        """ User that is not owner of the order tries to create an order payment gets 403"""
        response = self.client.post(reverse('manage-order-payment-list'), self.order_payment_data,
                                   HTTP_AUTHORIZATION=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_payment_methods_unauthenticated(self):
        """ Test that  unauthenticated users may retrieve payment methods """
        response = self.client.get(reverse('payment-method-list'), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_payment_methods_authenticated(self):
        """ Test that authenticated users may retrieve payment methods """
        response = self.client.get(reverse('payment-method-list'), {}, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_payment_method_detail_unauthenticated(self):
        """ Test that unauthenticated users may retrieve details of a payment method """
        self.skipTest("This view is currently unused")
        response = self.client.get(reverse('payment-method-list'), {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_payment_method_detail_authenticated(self):
        """ Test that authenticated users may retrieve details of a payment methods """
        self.skipTest("This view is currently unused")
        response = self.client.get(reverse('payment-method-list'), {}, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

