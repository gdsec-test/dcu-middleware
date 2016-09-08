import logging
from datetime import datetime

import mongomock
from mock import patch
from nose.tools import assert_true, assert_equal, assert_false

from dcumiddleware.tickethelper import TicketHelper
from test_settings import TestingConfig


class TestTicketHelper(object):
    @classmethod
    def setup(cls):
        logging.getLogger('suds').setLevel(logging.INFO)
        app_settings = TestingConfig()
        cls._tickethelper = TicketHelper(app_settings)
        # replace collection with mock
        cls._tickethelper._db._mongo._collection = mongomock.MongoClient().db.collection
        cls._tickethelper._db.add_new_incident(1236, dict(sourceDomainOrIp='lmn.com'))
        cls._tickethelper._db.add_new_incident(1237, dict(sourceDomainOrIp='abc.com'))
        cls._tickethelper._db.add_new_incident(1237, dict(sourceDomainOrIp='xyz.com', fraud_hold_until=datetime(2016, 5, 11)))
        cls._tickethelper._db.add_new_incident(1238, dict(sourceDomainOrIp='cjh.com', fraud_hold_until=datetime(2025, 5, 11)))

    def test_get_ticket_domain(self):
	    assert_true('abc.com' == self._tickethelper.domain_for_ticket(1237))
