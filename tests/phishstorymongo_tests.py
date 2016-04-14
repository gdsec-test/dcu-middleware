import mongomock
from mock import patch
from nose.tools import assert_true

from dcumiddleware.phishstorymongo import MongoHelper
from dcumiddleware.phishstorymongo import PhishstoryDB
from dcumiddleware.phishstorymongo import PhishstoryMongo
from test_settings import TestingConfig


class TestPhishstoryMongo:

    @classmethod
    def setup_class(cls):
        cls._db = PhishstoryMongo(TestingConfig())
        # replace collection with mock
        cls._db._mongo._collection = mongomock.MongoClient().db.collection
        cls._db.add_new_incident(1234, dict(type='PHISHING', reporter='abc@123.com', valid=True))
        cls._db.add_new_incident(1235, dict(type='PHISHING', reporter='abc@xyz.com', valid=True))
        cls._db.add_new_incident(1236, dict(type='MALWARE', reporter='abc@xyz.com'))
        cls._db.add_new_incident(1237, dict(type='MALWARE', reporter='abc@xyz.com'))

    @patch.object(MongoHelper, "save_file")
    def test_add_crits_data(self, mocked_method):
        mocked_method.return_value = '987'
        source_id, screenshot_id = self._db.add_crits_data(('screenshot', 'sourcecode'))
        orig = dict(_id=1234, reporter='abc@123.com', type=PhishstoryDB.PHISHING, valid=True)
        assert_true(source_id=='987')
        assert_true(screenshot_id=='987')

    def test_get_open_tickets(self):
        lst = [data for data in self._db.get_open_tickets(PhishstoryDB.PHISHING)]
        assert_true(len(lst) == 2)

    def test_update_incident(self):
        document = self._db.update_incident(1235, dict(type=PhishstoryDB.PHISHING, reporter='def@456.net'))
        assert_true(document['type'] == 'PHISHING')
        assert_true(document['reporter'] == 'abc@xyz.com')
        document = self._db.update_incident(666, dict(type=PhishstoryDB.PHISHING, reporter='def@456.net'))
        assert_true(document is None)

    def test_get_incident(self):
        document = self._db.get_incident(1235)
        assert_true(document['type'] == 'PHISHING')
        assert_true(document['reporter'] == 'abc@xyz.com')