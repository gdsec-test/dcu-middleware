import mongomock
from dcdatabase.mongohelper import MongoHelper
from mock import patch
from nose.tools import assert_true

from dcumiddleware.phishingstrategy import PhishingStrategy
from dcumiddleware.urihelper import URIHelper
from test_settings import TestingConfig


class TestPhishingStrategy:

    @classmethod
    def setup_class(cls):
        config = TestingConfig()
        cls._phishing = PhishingStrategy(config)
        cls._urihelper = URIHelper(config)
        # Replace underlying db implementation with mock
        cls._phishing._db._mongo._collection = mongomock.MongoClient().db.collection

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    def test_process_hosted(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'comicsn.beer',
                        'ticketId': u'DCU000001053',
                        'reporter': u'bxberry',
                        'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
                        'type': u'PHISHING'}
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001053')
        assert_true(doc['ticketId'] == 'DCU000001053')
        assert_true(doc['hosted_status'] == 'HOSTED')

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    def test_process_foreign(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'google.com',
                        'ticketId': u'DCU000001054',
                        'reporter': u'bxberry',
                        'source': u'http://google.com',
                        'type': u'PHISHING'}
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001054')
        assert_true(doc['ticketId'] == 'DCU000001054')
        assert_true(doc['hosted_status'] == 'FOREIGN')
        assert_true(doc['phishstory_status'] == 'CLOSED')
        assert_true(doc['close_reason'] == 'unworkable')

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    def test_process_unknown(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'',
                        'ticketId': u'DCU000001055',
                        'reporter': u'bxberry',
                        'source': u'http://',
                        'type': u'PHISHING'}
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001055')
        assert_true(doc['ticketId'] == 'DCU000001055')
        assert_true(doc['hosted_status'] == 'UNKNOWN')
        assert_true(doc['phishstory_status'] == 'CLOSED')
        assert_true(doc['close_reason'] == 'unworkable')

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    def test_process_proxy(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'comicsn.beer',
                        'ticketId': u'DCU000001056',
                        'reporter': u'bxberry',
                        'source': u'http://',
                        'proxy': 'brazil',
                        'type': u'PHISHING'}
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001056')
        assert_true(doc['ticketId'] == 'DCU000001056')
