import mongomock
from mock import patch
from nose.tools import assert_true

from dcumiddleware.incident import Incident
from dcumiddleware.interfaces.phishstorydb import PhishstoryDB
from dcumiddleware.mongohelper import MongoHelper
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
    def test_process(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'domain': u'comicsn.beer',
                        'ticketId': u'DCU000001053',
                        'reporter': u'bxberry',
                        'sources': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
                        'type': u'PHISHING'}
        self._phishing.process(Incident(test_record))
        lst =  [doc for doc in self._phishing._db.get_open_tickets(PhishstoryDB.PHISHING)]
        assert_true(lst[0]['ticketId'] == 'DCU000001053')
