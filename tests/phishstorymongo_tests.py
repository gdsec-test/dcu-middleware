import mongomock
from nose.tools import assert_true

from dcumiddleware.phishstorymongo import PhishstoryMongo
from dcumiddleware.phishstorymongo import PhishstoryDB
from test_settings import TestingConfig


class TestPhishstoryMongo:

    @classmethod
    def setup_class(cls):
        cls._db = PhishstoryMongo(TestingConfig())
        # replace collection with mock
        cls._db._mongo._collection = mongomock.MongoClient().db.collection

    def test_get_open_tickets(self):
        self._db.add_new_incident(PhishstoryDB.PHISHING, dict(_id=1234, reporter='abc@123.com'))
        self._db.add_new_incident(PhishstoryDB.PHISHING, dict(_id=1235, reporter='abc@xyz.com'))
        self._db.add_new_incident(PhishstoryDB.MALWARE, dict(_id=1236, reporter='abc@xyz.com'))
        lst = [data for data in self._db.get_open_tickets(PhishstoryDB.PHISHING)]
        assert_true(len(lst) == 2)
