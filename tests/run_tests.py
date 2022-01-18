import socket
from unittest.case import TestCase

from dcdatabase.phishstorymongo import PhishstoryMongo
from mock import patch
from mock.mock import MagicMock
from nose.tools import (assert_dict_equal, assert_false, assert_is_none,
                        assert_true)
from pymongo.collection import Collection

import run
from dcumiddleware.apihelper import APIHelper

HOSTED = 'HOSTED'
KEY_BLACKLIST = 'blacklist'
KEY_FAILED_ENRICHMENT = 'failedEnrichment'
KEY_HOSTED = 'hosted_status'
KEY_PHISHSTORY_STATUS = 'phishstory_status'
KEY_SOURCE_DOMAIN = 'sourceDomainOrIp'
KEY_SUBDOMAIN = 'sourceSubDomain'
KEY_TICKET_ID = 'ticketId'
KEY_TYPE = 'type'
OPEN = 'OPEN'
PHISHING = 'PHISHING'

AUTO_SUSPEND_DOMAIN = {
    'source': 'https://test1.godaddysites.com/',
    KEY_SOURCE_DOMAIN: 'godaddysites.com',
    KEY_SUBDOMAIN: 'test1.godaddysites.com',
    KEY_TICKET_ID: 'DCU001',
    KEY_PHISHSTORY_STATUS: OPEN,
    KEY_HOSTED: HOSTED,
    KEY_TYPE: PHISHING,
    KEY_FAILED_ENRICHMENT: True,
}

NOT_BLACKLISTED_TICKET = {KEY_BLACKLIST: False}
BLACKLISTED_TICKET = {KEY_BLACKLIST: True}


class MockCmapServiceHelper:
    def __init__(self, _settings):
        pass

    def domain_query(self, _domain, _path):
        return {'status': 'good'}

    def api_cmap_merge(self, _dict1, _dict2):
        _return = dict()
        _return.update(_dict1)
        _return.update(_dict2)
        return _return


class TestRun(TestCase):
    FOREIGN_BRAND = 'FOREIGN'
    DATA_KEY = 'data'
    DOMAIN_QUERY_KEY = 'domainQuery'
    HOST_KEY = 'host'
    GUID_KEY = 'guid'
    PRODUCT_KEY = 'product'
    BRAND_KEY = 'brand'
    SHOPPER_KEY = 'shopperId'
    REGISTRAR_KEY = 'registrar'
    DOMAIN_KEY = 'domainId'
    SHOPPER_INFO_KEY = 'shopperInfo'

    def setUp(self):
        self.incident = {
            run.KEY_METADATA: {
                run.KEY_PRODUCT: 'test',
                run.KEY_GUID: 'test-guid'
            }
        }

        self.enrichment = {
            run.DATA_KEY: {
                run.DOMAIN_Q_KEY: {
                    run.HOST_KEY: {
                        run.KEY_PRODUCT: 'test',
                        run.KEY_GUID: 'test-guid'
                    }
                }
            }
        }

    # Test successful load and enrichment
    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    @patch('run.CmapServiceHelper', return_value=MockCmapServiceHelper({}))
    @patch.object(socket, 'gethostbyname', return_value='1.1.1.1')
    def test_load_and_enrich_data_success(self, mock_socket, mock_cmap, mock_db):
        run._load_and_enrich_data(AUTO_SUSPEND_DOMAIN)
        mock_socket.assert_called()
        mock_cmap.assert_called()
        mock_db.assert_called()

    def build_cmap_data_object(self, shopper_brand='GODADDY', shopper_id='123456', domain_brand='GODADDY', domain_id='123456', domain_shopper='123456'):
        data = {
            self.DATA_KEY: {
                self.DOMAIN_QUERY_KEY: {
                    self.HOST_KEY: {
                        self.BRAND_KEY: shopper_brand,
                        self.SHOPPER_KEY: shopper_id,
                        self.GUID_KEY: 'random',
                        self.PRODUCT_KEY: 'DIABLO'
                    },
                    self.REGISTRAR_KEY: {
                        self.BRAND_KEY: domain_brand,
                        self.DOMAIN_KEY: domain_id
                    },
                    self.SHOPPER_INFO_KEY: {
                        self.SHOPPER_KEY: domain_shopper
                    }
                }
            }
        }
        return data

    def test_enrichment_status_check_hosted_registered(self):
        data = self.build_cmap_data_object()
        status = run.enrichment_succeeded(data)
        assert_true(status)

    def test_enrichment_status_check_hosted_not_registered(self):
        data = self.build_cmap_data_object(domain_brand=self.FOREIGN_BRAND, domain_id=None)
        status = run.enrichment_succeeded(data)
        assert_true(status)

    def test_enrichment_status_check_not_hosted_not_registered(self):
        data = self.build_cmap_data_object(shopper_brand=self.FOREIGN_BRAND, shopper_id=None, domain_brand=self.FOREIGN_BRAND, domain_id=None)
        status = run.enrichment_succeeded(data)
        assert_true(status)

    def test_enrichment_status_check_not_hosted_registered(self):
        data = self.build_cmap_data_object(shopper_brand=self.FOREIGN_BRAND, shopper_id=None)
        status = run.enrichment_succeeded(data)
        assert_true(status)

    def test_enrichment_status_check_hosted_registered_no_shopper(self):
        data = self.build_cmap_data_object(shopper_id=None)
        status = run.enrichment_succeeded(data)
        assert_false(status)

    def test_enrichment_status_check_hosted_registered_no_domainid(self):
        data = self.build_cmap_data_object(domain_id=None)
        status = run.enrichment_succeeded(data)
        assert_false(status)

    def test_enrichment_status_check_hosted_registered_no_domain_shopper(self):
        data = self.build_cmap_data_object(domain_shopper=None)
        status = run.enrichment_succeeded(data)
        assert_false(status)

    def test_enrichment_status_check_hosted_registered_no_id(self):
        data = self.build_cmap_data_object(domain_id=None, shopper_id=None)
        status = run.enrichment_succeeded(data)
        assert_false(status)

    def test_enrichment_status_check_missing_fields(self):
        data = {self.DATA_KEY: {}}
        status = run.enrichment_succeeded(data)
        assert_true(status)

    def test_enrichment_status_check_hosted_no_guid(self):
        data = self.build_cmap_data_object()
        del data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.GUID_KEY]
        status = run.enrichment_succeeded(data)
        assert_false(status)

    def test_enrichment_status_check_hosted_no_product(self):
        data = self.build_cmap_data_object()
        del data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.PRODUCT_KEY]
        status = run.enrichment_succeeded(data)
        assert_false(status)

    def test_enrichment_status_check_hosted_non_registered_product(self):
        data = self.build_cmap_data_object()
        data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.PRODUCT_KEY] = 'Shortener'
        del data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.GUID_KEY]
        status = run.enrichment_succeeded(data)
        assert_true(status)

    @patch.object(Collection, 'find_one', return_value=None)
    def test_blacklist_is_false(self, mock_find_one):
        result = run._check_for_blacklist_auto_actions(NOT_BLACKLISTED_TICKET)
        mock_find_one.assert_not_called()
        assert_dict_equal(result, NOT_BLACKLISTED_TICKET)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com'})
    def test_blacklisted_no_action(self, mock_find_one, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_update_actions.assert_not_called()
        assert_dict_equal(result, BLACKLISTED_TICKET)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com', 'action': ['nonsense']})
    def test_invalid_action(self, mock_find_one, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_update_actions.assert_not_called()
        assert_dict_equal(result, BLACKLISTED_TICKET)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com', 'action': ['false_positive']})
    def test_fp_auto_action(self, mock_find_one, mock_close_incident, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        assert_is_none(result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com', 'action': ['resolved']})
    def test_resolved_auto_action(self, mock_find_one, mock_close_incident, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        assert_is_none(result)

    @patch('run.CmapServiceHelper')
    def test_validate_abuse_verified_matching(self, mock_cmap):
        mock_cmap.return_value = MagicMock()

        run.validate_abuse_verified(self.incident, self.enrichment, 'test.com', '127.0.0.1')
        assert_dict_equal(self.incident[run.KEY_METADATA], self.enrichment[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY])
        mock_cmap.return_value.product_lookup.assert_not_called()
        mock_cmap.return_value.shopper_lookup.assert_not_called()

    @patch('run.CmapServiceHelper')
    def test_validate_abuse_verified_mismatch(self, mock_cmap):
        mock_cmap.return_value = MagicMock(
            product_lookup=MagicMock(return_value={run.KEY_SHOPPER_ID: 'test_shopper'}),
            shopper_lookup=MagicMock(return_value={'dummy': 'random'})
        )
        self.enrichment[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY][run.KEY_PRODUCT] = 'random'
        run.validate_abuse_verified(self.incident, self.enrichment, 'test.com', '127.0.0.1')
        mock_cmap.return_value.product_lookup.assert_called_with('test.com', 'test-guid', '127.0.0.1', 'test')
        mock_cmap.return_value.shopper_lookup.assert_called_with('test_shopper')
        assert_dict_equal(
            self.enrichment[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY],
            {'dummy': 'random', 'shopperId': 'test_shopper'}
        )
