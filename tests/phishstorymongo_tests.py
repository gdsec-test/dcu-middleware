import mongomock
from mock import patch
from nose.tools import assert_true

from dcumiddleware.phishstorymongo import PhishstoryDB
from dcumiddleware.phishstorymongo import PhishstoryMongo
from dcumiddleware.phishstorymongo import MongoHelper
from test_settings import TestingConfig


class TestPhishstoryMongo:

    @classmethod
    def setup_class(cls):
        cls._db = PhishstoryMongo(TestingConfig())
        # replace collection with mock
        cls._db._mongo._collection = mongomock.MongoClient().db.collection
        cls._db.add_new_incident(PhishstoryDB.PHISHING, dict(_id=1234, reporter='abc@123.com'))
        cls._db.add_new_incident(PhishstoryDB.PHISHING, dict(_id=1235, reporter='abc@xyz.com'))
        cls._db.add_new_incident(PhishstoryDB.MALWARE, dict(_id=1236, reporter='abc@xyz.com'))
        cls._db.add_new_incident(PhishstoryDB.MALWARE, dict(_id=1237, reporter='abc@xyz.com'))

    @patch.object(MongoHelper, "save_file")
    def test_add_crits_data(self, mocked_method):
        mocked_method.return_value = '987'
        document = self._db.add_crits_data(1234, ('screenshot', 'sourcecode'))
        assert_true(document == dict(_id=1234, reporter='abc@123.com', type=PhishstoryDB.PHISHING))
        document = self._db.add_crits_data(666, ())
        assert_true(document is None)

    def test_get_open_tickets(self):
        lst = [data for data in self._db.get_open_tickets(PhishstoryDB.PHISHING)]
        assert_true(len(lst) == 2)

    def test_find_incidents_by_and(self):
        lst = [data for data in self._db.find_incidents(dict(type=PhishstoryDB.MALWARE, reporter='abc@xyz.com'))]
        assert_true(len(lst) == 2)

    def test_find_incidents_by_or(self):
        lst = [data for data in self._db.find_incidents(dict(type=PhishstoryDB.MALWARE, reporter='abc@xyz.com'), False)]
        assert_true(len(lst) == 3)

    def test_update_incident(self):
        document = self._db.update_incident(1234, dict(type=PhishstoryDB.PHISHING, reporter='def@456.net'))
        assert_true(document == dict(_id=1234, reporter='abc@123.com', type=PhishstoryDB.PHISHING))
        document = self._db.update_incident(666, dict(type=PhishstoryDB.PHISHING, reporter='def@456.net'))
        assert_true(document is None)
