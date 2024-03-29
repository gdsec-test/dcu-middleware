import socket
from unittest.case import TestCase

from dcdatabase.phishstorymongo import PhishstoryMongo
from mock import patch
from mock.mock import MagicMock
from pymongo.collection import Collection

from dcumiddleware import run
from dcumiddleware.utilities.apihelper import APIHelper
from dcumiddleware.utilities.cmapv2helper import CmapV2Helper

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

CLOSED_TICKET = {
    'phishstory_status': 'CLOSED',
    'ticketId': 'DCU001',
}

OPEN_TICKET = {
    'phishstory_status': OPEN,
    'ticketId': 'DCU001',
}


class MockCmapServiceHelper:
    def __init__(self, _settings):
        self._path = None

    def domain_query(self, _domain, _path):
        self._path = _path
        return {'status': 'good'}

    def api_cmap_merge(self, _dict1, _dict2, _dict3, _dict4):
        _return = dict()
        _return.update(_dict1)
        _return.update(_dict2)
        _return.update(_dict3)
        _return.update(_dict4)
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
    cmapv2_data = {
        "customers": {
            "one customer id": {
                "createdDate": "2018-05-01",
                "plid": 1,
                "vip": False,
                "blacklist": False,
                "parentCustomerId": "",
                "attributes": {
                    "domainCount": 13,
                    "vipPortfolio": ""
                }
            }
        },
        "products": {
            "first product id": {
                "customerId": "one customer id",
                "createdDate": "2018-05-01",
                "plid": 1,
                "vip": False,
                "blacklist": False,
                "product": "GoCentral",
                "attributes": {
                    "vipPortfolio": "",
                    "dataCenter": None,
                    "containerId": None,
                    "hostname": None,
                    "ip": "ip-str",
                    "os": "Linux",
                    "mwpId": None,
                    "friendlyName": None,
                    "username": None,
                    "managedLevel": None
                },
                "associatedProducts": [
                    "second product id",
                    "third product id"
                ]
            },
            "second product id": {
                "customerId": "one customer id",
                "createdDate": "2018-05-01",
                "plid": 1,
                "vip": False,
                "blacklist": False,
                "product": "Standard SSL",
                "attributes": {
                    "certCommonName": None,
                    "createdAt": "2023-07-10",
                    "expiresAt": "2024-07-09"
                },
                "associatedProducts": []
            }},
        "brand": "GODADDY",
        "hostingCompanyName": "GoDaddy.com LLC",
        "abuseEmail": "abuse@godaddy.com"
    }

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
        self.cmapv2service = CmapV2Helper('mock_service_url', 'mock_sso_host', 'mock_client_cert_path', 'mock_client_key_path')

    # Test sync_attribute
    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    def test_sync_attribute(self, mock_db):
        run.sync_attribute(KEY_TICKET_ID, 'field', 'value')
        mock_db.assert_called_with(KEY_TICKET_ID, {'field': 'value'})

    # Test successful load and enrichment
    @patch('csetutils.services.jwt_base.post')
    @patch('dcumiddleware.utilities.cmapv2helper.requests.get')
    @patch.object(PhishstoryMongo, 'remove_field', return_value=None)
    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    @patch.object(PhishstoryMongo, 'get_incident', return_value=AUTO_SUSPEND_DOMAIN)
    @patch('dcumiddleware.run.CmapServiceHelper', return_value=MockCmapServiceHelper({}))
    @patch.object(socket, 'gethostbyname', return_value='1.1.1.1')
    def test_load_and_enrich_data_success(self, mock_socket, mock_cmap, mock_db_update, mock_db_remove, mock_db_get, mock_get, mock_post):
        mock_post.return_value = MagicMock(json=MagicMock(return_value={'data': 'mock_token'}))
        mock_get.return_value = MagicMock(json=MagicMock(return_value=self.cmapv2_data), status_code=200)
        run._load_and_enrich_data(AUTO_SUSPEND_DOMAIN)
        result = run.is_closed(AUTO_SUSPEND_DOMAIN[KEY_TICKET_ID])
        mock_socket.assert_called()
        self.assertEqual(mock_cmap.return_value._path, '/test%20me')
        self.assertFalse(result)
        mock_db_update.assert_called()
        mock_db_remove.assert_called()
        mock_db_get.assert_called()
        mock_get.assert_called_with('https://cmapv2.cset.int.test-gdcorp.tools/v1/cmap/lookupByHostAuthority?host=test1.godaddysites.com', headers={'Authorization': 'sso-jwt mock_token', 'Content-Type': 'application/json'})

    @patch('csetutils.services.jwt_base.post')
    @patch('dcumiddleware.utilities.cmapv2helper.requests.get')
    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    @patch('dcumiddleware.run.CmapServiceHelper')
    @patch.object(socket, 'gethostbyname', return_value='1.1.1.1')
    def test_load_and_enrich_entitlement(self, mock_socket, mock_cmap, mock_db, mock_get, mock_post):
        mock_post.return_value = MagicMock(json=MagicMock(return_value={'data': 'mock_token'}))
        mock_get.return_value = MagicMock(json=MagicMock(return_value=self.cmapv2_data), status_code=200)
        mock_cmap.return_value = MagicMock(
            product_lookup_entitlement=MagicMock(return_value={run.KEY_SHOPPER_ID: 'test_shopper'}),
            domain_query=MagicMock(return_value={})
        )
        run._load_and_enrich_data(self.enrichment_with_entitlement)
        mock_socket.assert_called()
        mock_cmap.return_value.product_lookup_entitlement.assert_called_with('test-customer', 'test-entitlement')
        mock_db.assert_called()
        mock_get.assert_called_with('https://cmapv2.cset.int.test-gdcorp.tools/v1/cmap/lookupByHostAuthority?host=test1.godaddysites.com', headers={'Authorization': 'sso-jwt mock_token', 'Content-Type': 'application/json'})

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

    def test_enrichment_status_check_no_brand_with_domain_shopper(self):
        data = self.build_cmap_data_object(domain_brand=None, domain_shopper='123456')
        status = run.enrichment_succeeded(data)
        self.assertFalse(status)

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

    @patch.object(Collection, 'find_one')
    def test_blacklisted_user_gen(self, mock_find_one):
        mock_find_one.side_effect = [
            {'entity': 'test.com', 'category': 'godaddy_asset', 'action': 'resolved'},
            None,
            {'entity': '123456789', 'category': 'godaddy_asset', 'action': 'resolved'},
            {'entity': '987654321', 'category': 'user_gen', 'action': 'resolved'}
        ]
        result = run.get_blacklist_info('test.com', 'www.test.com', '123456789', '987654321')
        self.assertIsNone(result)
        mock_find_one.side_effect = [
            {'entity': 'test.com', 'category': 'godaddy_asset', 'action': 'resolved'},
            None,
            {'entity': '123456789', 'category': 'user_gen', 'action': 'resolved'},
            {'entity': '987654321', 'category': 'godaddy_asset', 'action': 'resolved'}
        ]
        result = run.get_blacklist_info('test.com', 'www.test.com', '123456789', '987654321')
        self.assertIsNone(result)
        mock_find_one.side_effect = [
            {'entity': 'test.com', 'category': 'user_gen', 'action': 'resolved'},
            None,
            {'entity': '123456789', 'category': 'godaddy_asset', 'action': 'resolved'},
            {'entity': '987654321', 'category': 'godaddy_asset', 'action': 'resolved'}
        ]
        result = run.get_blacklist_info('test.com', 'www.test.com', '123456789', '987654321')
        self.assertIsNone(result)
        mock_find_one.side_effect = [
            {'entity': 'test.com', 'category': 'godaddy_asset', 'action': 'resolved'},
            None,
            {'entity': '123456789', 'category': 'godaddy_asset', 'action': 'resolved'},
            {'entity': '987654321', 'category': 'godaddy_asset', 'action': 'resolved'}
        ]
        result = run.get_blacklist_info('test.com', 'www.test.com', '123456789', '987654321')
        self.assertEqual(result, 'resolved')

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
    @patch.object(Collection, 'find_one', return_value={'entity': 'test.com', 'action': ['resolved_no_action']})
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
    @patch.object(Collection, 'find_one', side_effect=[None, None, {'entity': 'test.com', 'action': ['false_positive']}, None])
    def test_host_shopper_only_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY] = {run.SHOPPER_KEY: 'test'}
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, None, None, {'entity': 'test.com', 'action': ['false_positive']}])
    def test_domain_shopper_only_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.SHOPPER_INFO_KEY] = {run.SHOPPER_KEY: 'test'}
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, None, {'entity': 'test.com', 'action': ['false_positive']}, {'entity': 'test.com', 'action': ['false_positive']}, None])
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
    @patch.object(Collection, 'find_one', side_effect=[None, None, None, None])
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
    @patch.object(Collection, 'find_one', side_effect=[None, None, None, None])
    def test_failed_enrichment_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.SHOPPER_INFO_KEY] = {run.SHOPPER_KEY: 'test'}
        self.BLACKLISTED_TICKET[run.DATA_KEY][run.DOMAIN_Q_KEY][run.HOST_KEY] = {run.SHOPPER_KEY: 'test'}
        self.BLACKLISTED_TICKET[run.FAILED_ENRICHMENT_KEY] = True
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_not_called()
        mock_close_incident.assert_not_called()
        mock_update_actions.assert_not_called()
        self.assertEqual(self.BLACKLISTED_TICKET, result)

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(APIHelper, 'close_incident', return_value=None)
    @patch.object(Collection, 'find_one', side_effect=[None, {'entity': 'www.test.com', 'action': ['false_positive']}, None, None])
    def test_subdomain_only_bl(self, mock_find_one, mock_close_incident, mock_update_actions):
        self.BLACKLISTED_TICKET['sourceSubDomain'] = 'www.test.com'
        result = run._check_for_blacklist_auto_actions(self.BLACKLISTED_TICKET)
        mock_find_one.assert_called()
        mock_close_incident.assert_called()
        mock_update_actions.assert_called()
        self.assertIsNone(result)

    def test_cmapv2Data_mapped(self):
        doc = self.cmapv2service.convert_cmapv2data({'productData': self.cmapv2_data})
        self.assertTrue('domainQuery' in doc['cmapv2Data'])
        self.assertTrue('apiReseller' in doc['cmapv2Data']['domainQuery'])
        self.assertTrue('securitySubscription' in doc['cmapv2Data']['domainQuery'])
        self.assertTrue('sslSubscription' in doc['cmapv2Data']['domainQuery'])
        self.assertTrue('host' in doc['cmapv2Data']['domainQuery'])
        self.assertTrue('registrar' in doc['cmapv2Data']['domainQuery'])
        self.assertTrue('shopperInfo' in doc['cmapv2Data']['domainQuery'])
        self.assertTrue('hostname' in doc['cmapv2Data']['domainQuery']['host'])
        self.assertTrue('vipPortfolio' in doc['cmapv2Data']['domainQuery']['host']['vip'])
        self.assertTrue('brand' in doc['cmapv2Data']['domainQuery']['registrar'])
        self.assertTrue('abuseReportEmail' in doc['cmapv2Data']['domainQuery']['registrar'])
        self.assertTrue(doc['cmapv2Data']['domainQuery']['apiReseller']['parentCustomerId'] == 'one customer id')
        self.assertTrue(doc['cmapv2Data']['domainQuery']['host']['entitlementId'] == 'first product id')
        self.assertTrue(doc['cmapv2Data']['domainQuery']['securitySubscription']['products'] == ['first product id'])
        self.assertTrue(doc['cmapv2Data']['domainQuery']['sslSubscription'] == ['second product id'])
        self.assertTrue(self.cmapv2service.convert_cmapv2data(None) is None)
        self.assertTrue(self.cmapv2service.convert_cmapv2data({}) is None)

        cmapv2_data = {'cmapv2Data': 'productData'}
        with self.assertRaises(Exception):
            self.cmapv2service.convert_cmapv2data(cmapv2_data)

    # Test get_incident
    # Test don't update closed tickets, is_closed returns True
    @patch('csetutils.services.jwt_base.post')
    @patch.object(PhishstoryMongo, 'get_incident', return_value=CLOSED_TICKET)
    def test_closed_ticket_no_enrichment(self, mock_db, mock_post):
        mock_post.return_value = MagicMock(json=MagicMock(return_value={'data': 'mock_token'}))
        result = run.is_closed(CLOSED_TICKET['ticketId'])
        mock_db.assert_called_with(CLOSED_TICKET['ticketId'])
        self.assertTrue(result)

    # Test get_incident
    # Test don't update closed tickets, is_closed returns False
    @patch('csetutils.services.jwt_base.post')
    @patch.object(PhishstoryMongo, 'get_incident', return_value=OPEN_TICKET)
    def test_open_ticket_yes_enrichment(self, mock_db, mock_post):
        mock_post.return_value = MagicMock(json=MagicMock(return_value={'data': 'mock_token'}))
        result = run.is_closed(OPEN_TICKET['ticketId'])
        mock_db.assert_called_with(OPEN_TICKET['ticketId'])
        self.assertFalse(result)

    # Test get_incident
    # Test don't update closed tickets, is_closed returns None
    @patch('csetutils.services.jwt_base.post')
    @patch.object(PhishstoryMongo, 'get_incident', return_value=None)
    def test_no_ticket_found_no_enrichment(self, mock_db, mock_post):
        mock_post.return_value = MagicMock(json=MagicMock(return_value={'data': 'mock_token'}))
        result = run.is_closed(None)
        mock_db.assert_not_called()
        self.assertIsNone(result)
