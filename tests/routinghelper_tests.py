from nose.tools import assert_true
from celery import Celery
from celeryconfig import CeleryConfig

from dcumiddleware.routinghelper import RoutingHelper


class TestRoutingHelper:

    @classmethod
    def setup(cls):
        cls._routing_helper = RoutingHelper(Celery().config_from_object(CeleryConfig))

    def test_find_brands_to_route_no_host_no_registrar(self):
        brands = self._routing_helper._find_brands_to_route(None, None)
        assert_true(brands == ['GODADDY'])

    def test_find_brands_to_route_host_no_registrar_branded(self):
        brands = self._routing_helper._find_brands_to_route('GODADDY', None)
        assert_true(brands == ['GODADDY'])

    def test_find_brands_to_route_registrar_no_host_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, 'EMEA')
        assert_true(brands == ['EMEA'])

    def test_find_brands_to_route_registrar_no_host_not_branded(self):
        brands = self._routing_helper._find_brands_to_route(None, 'FOREIGN')
        assert_true(brands == ['FOREIGN'])

    def test_find_brands_to_route_host_no_registrar_not_branded(self):
        brands = self._routing_helper._find_brands_to_route('FOREIGN', None)
        assert_true(brands == ['FOREIGN'])

    def test_find_brands_to_route_registrar_and_host_both_branded_same(self):
        brands = self._routing_helper._find_brands_to_route('EMEA', 'EMEA')
        assert_true(brands == ['EMEA'])

    def test_find_brands_to_route_host_registrar_both_branded_different(self):
        brands = self._routing_helper._find_brands_to_route('GODADDY', 'EMEA')
        assert_true(brands == ['GODADDY', 'EMEA'])

    def test_find_brands_to_route_registrar_branded_hosted_not_branded(self):
        brands = self._routing_helper._find_brands_to_route('FOREIGN', 'EMEA')
        assert_true(brands == ['FOREIGN', 'EMEA'])

    def test_find_brands_to_route_foreign(self):
        brands = self._routing_helper._find_brands_to_route('FOREIGN', 'FOREIGN')
        assert_true(brands == ['FOREIGN'])
