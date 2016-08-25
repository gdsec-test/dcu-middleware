import logging

import mongomock
from dcdatabase.interfaces.phishstorydb import PhishstoryDB
from nose.tools import assert_true

from dcumiddleware.netabusestrategy import NetAbuseStrategy
from dcumiddleware.urihelper import URIHelper
from test_settings import TestingConfig


class TestNetabuseStrategy:

    @classmethod
    def setup_class(cls):
        config = TestingConfig()
        cls._netabuse = NetAbuseStrategy(config)
        cls._urihelper = URIHelper(config)
        # Replace underlying db implementation with mock
        cls._netabuse._db._mongo._collection = mongomock.MongoClient().db.collection
        logging.getLogger('suds').setLevel(logging.INFO)

    def test_process(self):
        test_record = { 'sourceDomainOrIp': u'160.153.77.227',
                        'ticketId': u'DCU000001053',
                        'reporter': u'bxberry',
                        'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
                        'type': u'NETABUSE',
                        'phishstory_status': u'OPEN',
                        'hosted_status': u'HOSTED'}
        self._netabuse.process(test_record)
        lst = [doc for doc in self._netabuse._db.get_tickets(PhishstoryDB.NETABUSE, "HOSTED", "OPEN")]
        assert_true(lst[0]['sourceDomainOrIp'] == '160.153.77.227')

        test_record2 = { 'sourceDomainOrIp': u'8.8.8.8',
                        'ticketId': u'DCU000001054',
                        'reporter': u'bxberry',
                        'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
                        'type': u'NETABUSE'}
        self._netabuse.process(test_record2)
        data = self._netabuse._db.get_incident("DCU000001054")
        assert_true(data['sourceDomainOrIp'] == '8.8.8.8')
