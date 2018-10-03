import mongomock
from celery import Celery
from dcdatabase.phishstorymongo import PhishstoryMongo
from mock import patch
from nose.tools import assert_equal, assert_true

from celeryconfig import CeleryConfig
from dcumiddleware.routinghelper import RoutingHelper
from settings import TestAppConfig


class TestRoutingHelper:

    @classmethod
    def setup(cls):
        cls._routing_helper = RoutingHelper(Celery().config_from_object(CeleryConfig), PhishstoryMongo(TestAppConfig()))
        cls._routing_helper._db._mongo._collection = mongomock.MongoClient().db.collection
        cls._routing_helper._db.add_new_incident(1234, dict(ticketId=1234))

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

    @patch.object(RoutingHelper, '_route_to_brand')
    def test_route_emea_only(self, _route_to_brand):
        ticket_data = {'ticketId': '1234', 'data': {'domainQuery': {'host': {'brand': 'EMEA'},
                                                                    'registrar': {'brand': 'EMEA'}}}}
        returned_data = self._routing_helper.route(ticket_data)

        assert_equal(returned_data, self._routing_helper._db.get_incident('1234'))

    @patch.object(RoutingHelper, '_route_to_brand')
    def test_route_godaddy_foreign(self, _route_to_brand):
        ticket_data = {'ticketId': '1234', 'data': {'domainQuery': {'host': {'brand': 'GODADDY'},
                                                                    'registrar': {'brand': 'FOREIGN'}}}}
        returned_data = self._routing_helper.route(ticket_data)

        assert_equal(returned_data, ticket_data)
