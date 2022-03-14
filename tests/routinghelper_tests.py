from unittest.case import TestCase

from celery import Celery
from mock import patch

from dcumiddleware.celeryconfig import CeleryConfig
from dcumiddleware.utilities.apihelper import APIHelper
from dcumiddleware.utilities.routinghelper import RoutingHelper
from dcumiddleware.settings import UnitTestAppConfig


class MockMongo:
    """
    Since RoutingHelper now needs a db handle passed to its constructor so it can run
    the update_actions_sub_document method... this is the "mocked" class that will be
    provided to it
    """
    def update_actions_sub_document(self, a, b):
        pass


class TestRoutingHelper(TestCase):
    REG123 = '123REG'
    EMEA = 'EMEA'
    FOREIGN = 'FOREIGN'
    GODADDY = 'GODADDY'
    KEY_BRAND = 'brand'
    KEY_DATA = 'data'
    KEY_DOMAIN_QUERY = 'domainQuery'
    KEY_HOST = 'host'
    KEY_REGISTRAR = 'registrar'
    KEY_TICKET_ID = 'ticketId'

    def setUp(self):
        self._routing_helper = RoutingHelper(Celery().config_from_object(CeleryConfig),
                                             APIHelper(UnitTestAppConfig()),
                                             MockMongo())

    def test_find_brands_to_route_no_host_no_registrar(self):
        brands = self._routing_helper._find_brands_to_route(None, None)
        self.assertEqual(brands, {self.GODADDY})

    def test_find_brands_to_route_host_no_registrar_branded(self):
        brands = self._routing_helper._find_brands_to_route(self.GODADDY, None)
        self.assertEqual(brands, {self.GODADDY})

    def test_find_brands_to_route_registrar_no_host_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, self.EMEA)
        self.assertEqual(brands, {self.EMEA})

    def test_find_brands_to_route_registrar_no_host_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, self.FOREIGN)
        self.assertEqual(brands, {self.FOREIGN})

    def test_find_brands_to_route_host_no_registrar_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(self.FOREIGN, None)
        self.assertEqual(brands, {self.FOREIGN})

    def test_find_brands_to_route_registrar_and_host_both_branded_same(self):
        brands = self._routing_helper._find_brands_to_route(self.EMEA, self.EMEA)
        self.assertEqual(brands, {self.EMEA})

    def test_find_brands_to_route_host_registrar_both_branded_different(self):
        brands = self._routing_helper._find_brands_to_route(self.GODADDY, self.EMEA)
        self.assertEqual(brands, {self.GODADDY, self.EMEA})

    def test_find_brands_to_route_registrar_branded_hosted_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(self.FOREIGN, self.EMEA)
        self.assertEqual(brands, {self.FOREIGN, self.EMEA})

    def test_find_brands_to_route_foreign(self):
        brands = self._routing_helper._find_brands_to_route(self.FOREIGN, self.FOREIGN)
        self.assertEqual(brands, {self.FOREIGN})

    def test_find_brands_to_route_123reg_hosted(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.EMEA)
        self.assertEqual(brands, {self.REG123, self.EMEA})

    def test_find_brands_to_route_123reg_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.EMEA, self.REG123)
        self.assertEqual(brands, {self.EMEA, self.REG123})

    def test_find_brands_to_route_123reg_registered_and_hosted(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.REG123)
        self.assertEqual(brands, {self.REG123})

    def test_find_brands_to_route_123reg_hosted_foreign_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.FOREIGN)
        self.assertEqual(brands, {self.GODADDY})

    def test_find_brands_to_route_gd_hosted_foreign_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.GODADDY, self.FOREIGN)
        self.assertEqual(brands, {self.GODADDY})

    def test_find_brands_to_route_123reg_hosted_gd_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.GODADDY)
        self.assertEqual(brands, {self.GODADDY})

    @patch.object(APIHelper, 'close_incident')
    def test_close_emea_only_ticket(self, mock_api):
        ticket_data = {self.KEY_TICKET_ID: '1234', self.KEY_DATA: {
            self.KEY_DOMAIN_QUERY: {
                self.KEY_HOST: {self.KEY_BRAND: self.EMEA},
                self.KEY_REGISTRAR: {self.KEY_BRAND: self.EMEA}
            }
        }}
        self.assertIsNone(self._routing_helper._close_emea_only_ticket(ticket_data))

    @patch.object(RoutingHelper, '_route_to_brand')
    def test_route_godaddy(self, _route_to_brand):
        ticket_data = {self.KEY_TICKET_ID: '1235', self.KEY_DATA: {
            self.KEY_DOMAIN_QUERY: {
                self.KEY_HOST: {self.KEY_BRAND: self.GODADDY},
                self.KEY_REGISTRAR: {self.KEY_BRAND: self.FOREIGN}
            }
        }}
        returned_data = self._routing_helper.route(ticket_data)
        self.assertEqual(returned_data, ticket_data)
