from nose.tools import assert_true
from mock import patch

from celery import Celery
from celeryconfig import CeleryConfig
from dcumiddleware.routinghelper import RoutingHelper


class TestRoutingHelper:

    @classmethod
    def setup(cls):
        cls._routing_helper = RoutingHelper(Celery().config_from_object(CeleryConfig))

    @patch.object(Celery, 'send_task')
    def test_route_no_host_no_registrar(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route(None, None, {'ticketId': "test_ticket"})
        assert_true(brands == ['GODADDY'])

    @patch.object(Celery, 'send_task')
    def test_route_host_no_registrar_branded(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route('GODADDY', None, {'ticketId': "test_ticket"})
        assert_true(brands == ['GODADDY'])

    @patch.object(Celery, 'send_task')
    def test_route_registrar_no_host_branded(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route(None, 'EMEA', {'ticketId': "test_ticket"})
        assert_true(brands == ['EMEA'])

    @patch.object(Celery, 'send_task')
    def test_route_registrar_no_host_not_branded(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route(None, 'FOREIGN', {'ticketId': "test_ticket"})
        assert_true(brands == ['FOREIGN'])

    @patch.object(Celery, 'send_task')
    def test_route_host_no_registrar_not_branded(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route('FOREIGN', None, {'ticketId': "test_ticket"})
        assert_true(brands == ['FOREIGN'])

    @patch.object(Celery, 'send_task')
    def test_route_registrar_and_host_both_branded_same(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route('EMEA', 'EMEA', {'ticketId': "test_ticket"})
        assert_true(brands == ['EMEA'])

    @patch.object(Celery, 'send_task')
    def test_route_host_registrar_both_branded_different(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route('GODADDY', 'EMEA', {'ticketId': "test_ticket"})
        assert_true(brands == ['GODADDY', 'EMEA'])

    @patch.object(Celery, 'send_task')
    def test_route_registrar_branded_hosted_not_branded(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route('FOREIGN', 'EMEA', {'ticketId': "test_ticket"})
        assert_true(brands == ['FOREIGN', 'EMEA'])

    @patch.object(Celery, 'send_task')
    def test_route_foreign(self, send_task):
        send_task.return_value = True
        brands = self._routing_helper.route('FOREIGN', 'FOREIGN', {'ticketId': "test_ticket"})
        assert_true(brands == ['FOREIGN'])
