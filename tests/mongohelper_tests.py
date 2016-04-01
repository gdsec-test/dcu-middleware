import mongomock
from nose.tools import assert_true

from dcumiddleware.mongohelper import MongoHelper
from test_settings import TestingConfig


class TestMongoHelper:

    @classmethod
    def setup_class(cls):
        cls._db = MongoHelper(TestingConfig())
        # replace collection with mock
        cls._db._collection = mongomock.MongoClient().db.collection

    def test_add_incident(self):
        _id = self._db.add_incident(dict(_id=1234,type='PHISHING'))
        assert_true(_id==1234)

    def test_find_incident(self):
        self._db.add_incident(dict(_id=1234,type='PHISHING'))
        doc = self._db.find_incident(dict(type='PHISHING'))
        assert_true(doc['_id']==1234)

    def test_find_incidents(self):
        self._db.add_incident(dict(_id=1234,type='PHISHING'))
        self._db.add_incident(dict(_id=1235,type='PHISHING'))
        docs = self._db.find_incidents(dict(type='PHISHING'))
        lst = [doc for doc in docs]
        assert_true(len(lst)==2)

    def test_replace_incident(self):
        self._db.add_incident(dict(_id=1234,type='PHISHING'))
        doc = self._db.find_incident(dict(type='PHISHING'))
        doc['type'] = 'MALWARE'
        doc = self._db.replace_incident(1234, doc)
        assert_true(doc['type']=='PHISHING')  # old version
        doc = self._db.find_incident(dict(type='MALWARE'))
        assert_true(doc['_id'] == 1234)

    def test_update_incident(self):
        self._db.add_incident(dict(_id=12345,type='PHISHING'))
        doc = self._db.update_incident(12345, dict(type='MALWARE'))
        assert_true(doc['type']=='PHISHING')  # old version
        doc = self._db.find_incident(dict(_id=12345))
        assert_true(doc['type'] == 'MALWARE')
