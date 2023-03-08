import socket
from unittest.case import TestCase

from dcdatabase.phishstorymongo import PhishstoryMongo
from mock import patch
from mock.mock import MagicMock
from pymongo.collection import Collection

from dcumiddleware import run
from dcumiddleware.utilities.apihelper import APIHelper

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
    'source': 'https://test1.godaddysites.com/test me',
    KEY_SOURCE_DOMAIN: 'godaddysites.com',
    KEY_SUBDOMAIN: 'test1.godaddysites.com',
    KEY_TICKET_ID: 'DCU001',
    KEY_PHISHSTORY_STATUS: OPEN,
    KEY_HOSTED: HOSTED,
    KEY_TYPE: PHISHING,
    KEY_FAILED_ENRICHMENT: True,
}


class MockCmapServiceHelper:
    def __init__(self, _settings):
        self._path = None

    def domain_query(self, _domain, _path):
        self._path = _path
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
    CUSTOMER_KEY = 'customerId'
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

        self.enrichment_with_entitlement = {
            'source': 'https://test1.godaddysites.com/test me',
            KEY_SOURCE_DOMAIN: 'godaddysites.com',
            KEY_SUBDOMAIN: 'test1.godaddysites.com',
            KEY_TICKET_ID: 'DCU001',
            KEY_PHISHSTORY_STATUS: OPEN,
            KEY_HOSTED: HOSTED,
            KEY_TYPE: PHISHING,
            run.KEY_METADATA: {
                run.KEY_PRODUCT: 'test',
                run.KEY_GUID: 'test-guid',
                run.KEY_CUSTOMER_ID: 'test-customer',
                run.KEY_ENTITLEMENT_ID: 'test-entitlement'
            }
        }

        self.NOT_BLACKLISTED_TICKET = {run.DATA_KEY: {run.DOMAIN_Q_KEY: {KEY_BLACKLIST: False}}}
        self.BLACKLISTED_TICKET = {run.DATA_KEY: {run.DOMAIN_Q_KEY: {KEY_BLACKLIST: True}}}

    # Test sync_attribute
    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    def test_sync_attribute(self, mock_db):
        run.sync_attribute(KEY_TICKET_ID, 'field', 'value')
        mock_db.assert_called_with(KEY_TICKET_ID, {'field': 'value'})

    # Test successful load and enrichment
    @patch.object(PhishstoryMongo, 'remove_field', return_value=None)
    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    @patch('dcumiddleware.run.CmapServiceHelper', return_value=MockCmapServiceHelper({}))
    @patch.object(socket, 'gethostbyname', return_value='1.1.1.1')
    def test_load_and_enrich_data_success(self, mock_socket, mock_cmap, mock_db_update, mock_db_remove):
        run._load_and_enrich_data(AUTO_SUSPEND_DOMAIN)
        mock_socket.assert_called()
        self.assertEqual(mock_cmap.return_value._path, '/test%20me')
        mock_db_update.assert_called()
        mock_db_remove.assert_called()

    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    @patch('dcumiddleware.run.CmapServiceHelper')
    @patch.object(socket, 'gethostbyname', return_value='1.1.1.1')
    def test_load_and_enrich_entitlement(self, mock_socket, mock_cmap, mock_db):
        mock_cmap.return_value = MagicMock(
            product_lookup_entitlement=MagicMock(return_value={run.KEY_SHOPPER_ID: 'test_shopper'}),
            domain_query=MagicMock(return_value={})
        )
        run._load_and_enrich_data(self.enrichment_with_entitlement)
        mock_socket.assert_called()
        mock_cmap.return_value.product_lookup_entitlement.assert_called_with('test-customer', 'test-entitlement')
        mock_db.assert_called()

    def build_cmap_data_object(self, shopper_brand='GODADDY', shopper_id='123456', customer_id='123456', domain_brand='GODADDY', domain_id='123456', domain_shopper='123456', domain_customer='123456'):
        data = {
            self.DATA_KEY: {
                self.DOMAIN_QUERY_KEY: {
                    self.HOST_KEY: {
                        self.BRAND_KEY: shopper_brand,
                        self.SHOPPER_KEY: shopper_id,
                        self.CUSTOMER_KEY: customer_id,
                        self.GUID_KEY: 'random',
                        self.PRODUCT_KEY: 'DIABLO'
                    },
                    self.REGISTRAR_KEY: {
                        self.BRAND_KEY: domain_brand,
                        self.DOMAIN_KEY: domain_id
                    },
                    self.SHOPPER_INFO_KEY: {
                        self.SHOPPER_KEY: domain_shopper,
                        self.CUSTOMER_KEY: domain_customer
                    }
                }
            }
        }
        return data

    def test_enrichment_status_check_hosted_registered(self):
        data = self.build_cmap_data_object()
        status = run.enrichment_succeeded(data)
        self.assertTrue(status)

    def test_enrichment_status_check_hosted_not_registered(self):
        data = self.build_cmap_data_object(domain_brand=self.FOREIGN_BRAND, domain_id=None)
        status = run.enrichment_succeeded(data)
        self.assertTrue(status)

    def test_enrichment_status_check_not_hosted_not_registered(self):
        data = self.build_cmap_data_object(shopper_brand=self.FOREIGN_BRAND, shopper_id=None, domain_brand=self.FOREIGN_BRAND, domain_id=None)
        status = run.enrichment_succeeded(data)
        self.assertTrue(status)

    def test_enrichment_status_check_not_hosted_registered(self):
        data = self.build_cmap_data_object(shopper_brand=self.FOREIGN_BRAND, shopper_id=None)
        status = run.enrichment_succeeded(data)
        self.assertTrue(status)

    def test_enrichment_status_check_hosted_registered_no_shopper(self):
        data = self.build_cmap_data_object(shopper_id=None)
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrich_status_check_hosted_registerd_no_customer(self):
        data = self.build_cmap_data_object(customer_id=None)
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrichment_status_check_hosted_registered_no_domainid(self):
        data = self.build_cmap_data_object(domain_id=None)
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrichment_status_check_hosted_registered_no_domain_shopper(self):
        data = self.build_cmap_data_object(domain_shopper=None)
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrichment_status_check_hosted_registered_no_domain_customer(self):
        data = self.build_cmap_data_object(domain_customer=None)
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrichment_status_check_hosted_registered_no_id(self):
        data = self.build_cmap_data_object(domain_id=None, shopper_id=None)
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrichment_status_check_missing_fields(self):
        data = {self.DATA_KEY: {}}
        status = run.enrichment_succeeded(data)
        self.assertTrue(status)

    def test_enrichment_status_check_hosted_no_guid(self):
        data = self.build_cmap_data_object()
        del data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.GUID_KEY]
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrichment_status_check_hosted_no_product(self):
        data = self.build_cmap_data_object()
        del data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.PRODUCT_KEY]
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

    def test_enrichment_status_check_hosted_non_registered_product(self):
        data = self.build_cmap_data_object()
        data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.PRODUCT_KEY] = 'Shortener'
        del data[self.DATA_KEY][self.DOMAIN_QUERY_KEY][self.HOST_KEY][self.GUID_KEY]
        status = run.enrichment_succeeded(data)
        self.assertTrue(status)

    @patch.object(Collection, 'find_one', return_value=None)
    def test_blacklist_is_false(self, mock_find_one):
        result = run._check_for_blacklist_auto_actions(self.NOT_BLACKLISTED_TICKET)
        mock_find_one.assert_not_called()
        self.assertDictEqual(result, self.NOT_BLACKLISTED_TICKET)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com'})
    def test_blacklisted_no_action(self, mock_find_one, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_update_actions.assert_not_called()
        self.assertDictEqual(result, self.BLACKLISTED_TICKET)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com', 'action': ['nonsense']})
    def test_invalid_action(self, mock_find_one, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_update_actions.assert_not_called()
        self.assertDictEqual(result, self.BLACKLISTED_TICKET)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com', 'action': ['false_positive']})
    def test_fp_auto_action(self, mock_find_one, mock_close_incident, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com', 'action': ['resolved']})
    def test_resolved_auto_action(self, mock_find_one, mock_close_incident, mock_update_actions):
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    @patch('dcumiddleware.run.CmapServiceHelper')
    def test_validate_abuse_verified_matching(self, mock_cmap):
        mock_cmap.return_value = MagicMock()

        run.validate_abuse_verified(self.incident, self.enrichment, 'test.com', '127.0.0.1')
        self.assertDictEqual(self.incident[run.KEY_METADATA], self.enrichment[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY])
        mock_cmap.return_value.product_lookup.assert_not_called()
        mock_cmap.return_value.shopper_lookup.assert_not_called()

    @patch('dcumiddleware.run.CmapServiceHelper')
    def test_validate_abuse_verified_mismatch(self, mock_cmap):
        mock_cmap.return_value = MagicMock(
            product_lookup=MagicMock(return_value={run.KEY_SHOPPER_ID: 'test_shopper'}),
            shopper_lookup=MagicMock(return_value={'dummy': 'random'})
        )
        self.enrichment[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY][run.KEY_PRODUCT] = 'random'
        run.validate_abuse_verified(self.incident, self.enrichment, 'test.com', '127.0.0.1')
        mock_cmap.return_value.product_lookup.assert_called_with('test.com', 'test-guid', '127.0.0.1', 'test')
        mock_cmap.return_value.shopper_lookup.assert_called_with('test_shopper')
        self.assertDictEqual(
            self.enrichment[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY],
            {'dummy': 'random', 'shopperId': 'test_shopper'}
        )

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, {'entity': 'test.com', 'action': ['false_positive']}, None])
    def test_host_shopper_only_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY] = {run.SHOPPER_KEY: 'test'}
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, None, {'entity': 'test.com', 'action': ['false_positive']}])
    def test_domain_shopper_only_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.SHOPPER_INFO_KEY] = {run.SHOPPER_KEY: 'test'}
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, {'entity': 'test.com', 'action': ['false_positive']}, {'entity': 'test.com', 'action': ['false_positive']}])
    def test_both_shopper_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.SHOPPER_INFO_KEY] = {run.SHOPPER_KEY: 'test'}
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY] = {run.SHOPPER_KEY: 'test'}
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, None, None])
    def test_no_shopper_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.SHOPPER_INFO_KEY] = {run.SHOPPER_KEY: 'test'}
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY] = {run.SHOPPER_KEY: 'test'}
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_not_called()
        mock_update_actions.assert_not_called()
        self.assertEqual(self.BLACKLISTED_TICKET, result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, None, None])
    def test_failed_enrichment_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.SHOPPER_INFO_KEY] = {run.SHOPPER_KEY: 'test'}
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY] = {run.SHOPPER_KEY: 'test'}
        self.BLACKLISTED_TICKET[run.FAILED_ENRICHMENT_KEY] = True
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_not_called()
        mock_close_incident.assert_not_called()
        mock_update_actions.assert_not_called()
        self.assertEqual(self.BLACKLISTED_TICKET, result)
