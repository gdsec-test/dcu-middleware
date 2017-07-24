from collections import namedtuple

import requests
from mock import patch
from nose.tools import assert_true, assert_false

from dcumiddleware.dcuapi_functions import DCUAPIFunctions
from test_settings import TestingConfig


class TestDCUAPIFunctions:

    @classmethod
    def setup_class(cls):
        cls._api = DCUAPIFunctions(TestingConfig())

    @patch.object(requests.Session, 'request')
    def test_close_ticket_success(self, mocked_method):
        data = dict(status_code = 204, content='SUCCESS')
        mocked_method.return_value = namedtuple('struct', data.keys())(**data)
        assert_true(self._api.close_ticket("DCU000001010"))

    @patch.object(requests.Session, 'request')
    def test_close_ticket_fail(self, mocked_method):
        data = dict(status_code = 500, content='FAIL')
        mocked_method.return_value = namedtuple('struct', data.keys())(**data)
        assert_false(self._api.close_ticket("DCU000001010"))
