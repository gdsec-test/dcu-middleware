from collections import namedtuple

from celery import Celery
from mock import patch
from nose.tools import assert_equal, assert_true

from celeryconfig import CeleryConfig
from dcumiddleware.apihelper import APIHelper
from dcumiddleware.routinghelper import RoutingHelper
from settings import TestAppConfig


class TestRoutingHelper:

    @classmethod
    def setup(cls):
        cls._routing_helper = RoutingHelper(Celery().config_from_object(CeleryConfig), APIHelper(TestAppConfig()))

    def test_find_brands_to_route_no_host_no_registrar(self):
        brands = self._routing_helper._find_brands_to_route(None, None)
        assert_equal(brands, {'GODADDY'})

    def test_find_brands_to_route_host_no_registrar_branded(self):
        brands = self._routing_helper._find_brands_to_route('GODADDY', None)
        assert_equal(brands, {'GODADDY'})

    def test_find_brands_to_route_registrar_no_host_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, 'EMEA')
        assert_equal(brands, {'EMEA'})

    def test_find_brands_to_route_registrar_no_host_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, 'FOREIGN')
        assert_equal(brands, {'FOREIGN'})

    def test_find_brands_to_route_host_no_registrar_not_branded(self):
        brands = self._routing_helper._find_brands_to_route('FOREIGN', None)
        assert_equal(brands, {'FOREIGN'})

    def test_find_brands_to_route_registrar_and_host_both_branded_same(self):
        brands = self._routing_helper._find_brands_to_route('EMEA', 'EMEA')
        assert_equal(brands, {'EMEA'})

    def test_find_brands_to_route_host_registrar_both_branded_different(self):
        brands = self._routing_helper._find_brands_to_route('GODADDY', 'EMEA')
        assert_equal(brands, {'GODADDY', 'EMEA'})

    def test_find_brands_to_route_registrar_branded_hosted_not_branded(self):
        brands = self._routing_helper._find_brands_to_route('FOREIGN', 'EMEA')
        assert_equal(brands, {'FOREIGN', 'EMEA'})

    def test_find_brands_to_route_foreign(self):
        brands = self._routing_helper._find_brands_to_route('FOREIGN', 'FOREIGN')
        assert_equal(brands, {'FOREIGN'})

    def test_find_brands_to_route_123reg_hosted(self):
        brands = self._routing_helper._find_brands_to_route('123REG', 'EMEA')
        assert_equal(brands, {'123REG', 'EMEA'})

    def test_find_brands_to_route_123reg_registered(self):
        brands = self._routing_helper._find_brands_to_route('EMEA', '123REG')
        assert_equal(brands, {'EMEA', '123REG'})

    def test_find_brands_to_route_123reg_registered_and_hosted(self):
        brands = self._routing_helper._find_brands_to_route('123REG', '123REG')
        assert_equal(brands, {'123REG'})

    def test_find_brands_to_route_123reg_hosted_foreign_registered(self):
        brands = self._routing_helper._find_brands_to_route('123REG', 'FOREIGN')
        assert_equal(brands, {'GODADDY'})

    def test_find_brands_to_route_gd_hosted_foreign_registered(self):
        brands = self._routing_helper._find_brands_to_route('GODADDY', 'FOREIGN')
        assert_equal(brands, {'GODADDY'})

    def test_find_brands_to_route_123reg_hosted_gd_registered(self):
        brands = self._routing_helper._find_brands_to_route('123REG', 'GODADDY')
        assert_equal(brands, {'GODADDY'})

    @patch.object(RoutingHelper, '_close_emea_only_ticket')
    def test_close_emea_only_ticket(self, _close_emea_only_ticket):
        ticket_data = {'ticketId': '1234', 'data': {'domainQuery': {'host': {'brand': 'EMEA'},
                                                                    'registrar': {'brand': 'EMEA'}}}}
        emea_only_ticket = self._routing_helper._close_emea_only_ticket(ticket_data)
        assert_true(emea_only_ticket)

    @patch.object(RoutingHelper, '_close_emea_only_ticket')
    def test_close_emea_only_ticket_fail(self, mocked_method):
        status = dict(status_code=500, status_message='FAIL')
        mocked_method.return_value = namedtuple('struct', status.keys())(**status)
        ticket_data = {'ticketId': '1236', 'data': {'domainQuery': {'host': {'brand': 'EMEA'},
                                                                    'registrar': {'brand': 'EMEA'}}}}
        emea_only_ticket_fail = self._routing_helper._close_emea_only_ticket(ticket_data)
        assert_true(emea_only_ticket_fail)

    @patch.object(RoutingHelper, '_route_to_brand')
    def test_route_godaddy(self, _route_to_brand):
        ticket_data = {'ticketId': '1235', 'data': {'domainQuery': {'host': {'brand': 'GODADDY'},
                                                                    'registrar': {'brand': 'FOREIGN'}}}}
        returned_data = self._routing_helper.route(ticket_data)
        assert_equal(returned_data, ticket_data)
