from datetime import datetime, timedelta

import mongomock
from dcdatabase.phishstorymongo import PhishstoryMongo
from nose.tools import assert_true, assert_false

from dcumiddleware.reviews import BasicReview, FraudReview
from test_settings import TestingConfig


class TestReview:

    def setUp(self):
        self._config = TestingConfig()
        self._db = PhishstoryMongo(self._config)
        # replace collection with mock
        self._db._mongo._collection = mongomock.MongoClient().db.collection
        self._db.add_new_incident(1234, dict(sourceDomainOrIp='abc.com', hold_until=datetime(2016, 5, 11)))
        self._db.add_new_incident(1235, dict(sourceDomainOrIp='xyz.com', hold_until=datetime.utcnow() + timedelta(hours=1)))
        self._db.add_new_incident(1236, dict(sourceDomainOrIp='lmn.com'))
        self._db.add_new_incident(1237, dict(sourceDomainOrIp='abc.com'))

        self._basic = BasicReview(self._config)
        self._basic._db = self._db  # Replace db with mock

        self._fraud = FraudReview(self._config)
        self._fraud._db = self._db  # Replace db with mock

    def test_basic_suspend(self):
        doc = self._basic.place_in_review(1236, self._config.HOLD_TIME)
        assert_true(doc['hold_until'])

    def test_new_fraud(self):
        doc = self._fraud.place_in_review(1236, self._config.HOLD_TIME)
        assert_true(doc['hold_until'])
        assert_true(doc['fraud_notified'])

    def test_existing_expired_fraud(self):
        doc = self._fraud.place_in_review(1234, self._config.HOLD_TIME)
        assert_true(doc['hold_until'] > datetime(2016, 5, 11))
        assert_true(doc['fraud_notified'])

    def test_existing_fraud(self):
        doc = self._fraud.place_in_review(1235, self._config.HOLD_TIME)
        assert_true(doc['hold_until'] < datetime.utcnow() + timedelta(hours=2))
        assert_false(doc.get('fraud_notified', None))
