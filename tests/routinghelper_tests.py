from celery import Celery
from mock import patch
from nose.tools import assert_equal, assert_is_none

from celeryconfig import CeleryConfig
from dcumiddleware.apihelper import APIHelper
from dcumiddleware.routinghelper import RoutingHelper
from settings import TestAppConfig


class MockMongo:
    """
    Since RoutingHelper now needs a db handle passed to its constructor so it can run
    the update_actions_sub_document method... this is the "mocked" class that will be
    provided to it
    """
    def update_actions_sub_document(self, a, b):
        pass


class TestRoutingHelper:
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

    @classmethod
    @patch.object(APIHelper, '_get_jwt')
    def setup(cls, mock_jwt):
        cls._routing_helper = RoutingHelper(Celery().config_from_object(CeleryConfig),
                                            APIHelper(TestAppConfig()),
                                            MockMongo())

    def test_find_brands_to_route_no_host_no_registrar(self):
        brands = self._routing_helper._find_brands_to_route(None, None)
        assert_equal(brands, {self.GODADDY})

    def test_find_brands_to_route_host_no_registrar_branded(self):
        brands = self._routing_helper._find_brands_to_route(self.GODADDY, None)
        assert_equal(brands, {self.GODADDY})

    def test_find_brands_to_route_registrar_no_host_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, self.EMEA)
        assert_equal(brands, {self.EMEA})

    def test_find_brands_to_route_registrar_no_host_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, self.FOREIGN)
        assert_equal(brands, {self.FOREIGN})

    def test_find_brands_to_route_host_no_registrar_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(self.FOREIGN, None)
        assert_equal(brands, {self.FOREIGN})

    def test_find_brands_to_route_registrar_and_host_both_branded_same(self):
        brands = self._routing_helper._find_brands_to_route(self.EMEA, self.EMEA)
        assert_equal(brands, {self.EMEA})

    def test_find_brands_to_route_host_registrar_both_branded_different(self):
        brands = self._routing_helper._find_brands_to_route(self.GODADDY, self.EMEA)
        assert_equal(brands, {self.GODADDY, self.EMEA})

    def test_find_brands_to_route_registrar_branded_hosted_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(self.FOREIGN, self.EMEA)
        assert_equal(brands, {self.FOREIGN, self.EMEA})

    def test_find_brands_to_route_foreign(self):
        brands = self._routing_helper._find_brands_to_route(self.FOREIGN, self.FOREIGN)
        assert_equal(brands, {self.FOREIGN})

    def test_find_brands_to_route_123reg_hosted(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.EMEA)
        assert_equal(brands, {self.REG123, self.EMEA})

    def test_find_brands_to_route_123reg_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.EMEA, self.REG123)
        assert_equal(brands, {self.EMEA, self.REG123})

    def test_find_brands_to_route_123reg_registered_and_hosted(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.REG123)
        assert_equal(brands, {self.REG123})

    def test_find_brands_to_route_123reg_hosted_foreign_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.FOREIGN)
        assert_equal(brands, {self.GODADDY})

    def test_find_brands_to_route_gd_hosted_foreign_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.GODADDY, self.FOREIGN)
        assert_equal(brands, {self.GODADDY})

    def test_find_brands_to_route_123reg_hosted_gd_registered(self):
        brands = self._routing_helper._find_brands_to_route(self.REG123, self.GODADDY)
        assert_equal(brands, {self.GODADDY})

    @patch.object(APIHelper, 'close_incident')
    def test_close_emea_only_ticket(self, mock_api):
        ticket_data = {self.KEY_TICKET_ID: '1234', self.KEY_DATA: {
            self.KEY_DOMAIN_QUERY: {
                self.KEY_HOST: {self.KEY_BRAND: self.EMEA},
                self.KEY_REGISTRAR: {self.KEY_BRAND: self.EMEA}
            }
        }}
        assert_is_none(self._routing_helper._close_emea_only_ticket(ticket_data))

    @patch.object(RoutingHelper, '_route_to_brand')
    def test_route_godaddy(self, _route_to_brand):
        ticket_data = {self.KEY_TICKET_ID: '1235', self.KEY_DATA: {
            self.KEY_DOMAIN_QUERY: {
                self.KEY_HOST: {self.KEY_BRAND: self.GODADDY},
                self.KEY_REGISTRAR: {self.KEY_BRAND: self.FOREIGN}
            }
        }}
        returned_data = self._routing_helper.route(ticket_data)
        assert_equal(returned_data, ticket_data)
