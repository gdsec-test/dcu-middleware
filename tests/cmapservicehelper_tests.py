from unittest.case import TestCase

from dateutil import parser
from mock import patch

from dcumiddleware.utilities.cmapservicehelper import CmapServiceHelper
from tests.test_settings import TestingConfig


class TestCmapServiceHelper(TestCase):
    def setUp(self):
        config = TestingConfig()
        self.cmapservice = CmapServiceHelper(config)

    @patch.object(CmapServiceHelper, 'cmap_query')
    def test_domain_query(self, cmap_query):
        cmap_query.return_value = {
            'data': {
                'domainQuery': {
                    'alexaRank': None,
                    'apiReseller': {
                        'child': None,
                        'parent': None
                    },
                    'blacklist': False,
                    'domain': 'example.com',
                    'securitySubscription': {
                        'sucuriProduct': None
                    },
                    'sslSubscriptions': {
                        'certCommonName': None,
                        'certType': None,
                        'createdAt': None,
                        'expiresAt': None
                    },
                    'host': {
                        'dataCenter': None,
                        'guid': None,
                        'containerId': None,
                        'hostingCompanyName': None,
                        'hostingAbuseEmail': [
                            None
                        ],
                        'hostname': None,
                        'ip': None,
                        'os': None,
                        'product': None,
                        'shopperId': None,
                        'shopperPlid': None,
                        'customerId': None,
                        'entitlementId': None,
                        'shopperCreateDate': '2003-01-19',
                        'privateLabelId': None,
                        'vip': {
                            'blacklist': False,
                            'portfolioType': None,
                            'shopperId': None
                        }
                    },
                    'registrar': {
                        'domainCreateDate': '2009-12-05',
                        'registrarAbuseEmail': [
                            None
                        ],
                        'registrarName': None
                    },
                    'shopperInfo': {
                        'domainCount': None,
                        'shopperCreateDate': '2003-01-19',
                        'shopperId': None,
                        'customerId': None,
                        'shopperPlid': None,
                        'vip': {
                            'blacklist': False,
                            'portfolioType': None,
                            'shopperId': None
                        }
                    }
                }
            }
        }
        domain = 'example.com'
        path = '/folder/file.ext'
        doc = self.cmapservice.domain_query(domain, path)
        self.assertTrue('data' in doc)
        self.assertTrue('domainQuery' in doc['data'])
        self.assertTrue('alexaRank' in doc['data']['domainQuery'])
        self.assertTrue('apiReseller' in doc['data']['domainQuery'])
        self.assertTrue('child' in doc['data']['domainQuery']['apiReseller'])
        self.assertTrue('parent' in doc['data']['domainQuery']['apiReseller'])
        self.assertTrue('blacklist' in doc['data']['domainQuery'])
        self.assertTrue('domain' in doc['data']['domainQuery'])
        self.assertTrue('securitySubscription' in doc['data']['domainQuery'])
        self.assertTrue('sslSubscriptions' in doc['data']['domainQuery'])
        self.assertTrue('certCommonName' in doc['data']['domainQuery']['sslSubscriptions'])
        self.assertTrue('certType' in doc['data']['domainQuery']['sslSubscriptions'])
        self.assertTrue('createdAt' in doc['data']['domainQuery']['sslSubscriptions'])
        self.assertTrue('expiresAt' in doc['data']['domainQuery']['sslSubscriptions'])
        self.assertTrue('host' in doc['data']['domainQuery'])
        self.assertTrue('dataCenter' in doc['data']['domainQuery']['host'])
        self.assertTrue('guid' in doc['data']['domainQuery']['host'])
        self.assertTrue('containerId' in doc['data']['domainQuery']['host'])
        self.assertTrue('hostingCompanyName' in doc['data']['domainQuery']['host'])
        self.assertTrue('hostingAbuseEmail' in doc['data']['domainQuery']['host'])
        self.assertTrue('hostname' in doc['data']['domainQuery']['host'])
        self.assertTrue('ip' in doc['data']['domainQuery']['host'])
        self.assertTrue('os' in doc['data']['domainQuery']['host'])
        self.assertTrue('product' in doc['data']['domainQuery']['host'])
        self.assertTrue('shopperId' in doc['data']['domainQuery']['host'])
        self.assertTrue('customerId' in doc['data']['domainQuery']['host'])
        self.assertTrue('entitlementId' in doc['data']['domainQuery']['host'])
        self.assertTrue('shopperPlid' in doc['data']['domainQuery']['host'])
        self.assertTrue('shopperCreateDate' in doc['data']['domainQuery']['host'])
        self.assertTrue('privateLabelId' in doc['data']['domainQuery']['host'])
        self.assertTrue('vip' in doc['data']['domainQuery']['host'])
        self.assertTrue('blacklist' in doc['data']['domainQuery']['host']['vip'])
        self.assertTrue('portfolioType' in doc['data']['domainQuery']['host']['vip'])
        self.assertTrue('shopperId' in doc['data']['domainQuery']['host']['vip'])
        self.assertTrue('registrar' in doc['data']['domainQuery'])
        self.assertTrue('domainCreateDate' in doc['data']['domainQuery']['registrar'])
        self.assertTrue('registrarAbuseEmail' in doc['data']['domainQuery']['registrar'])
        self.assertTrue('registrarName' in doc['data']['domainQuery']['registrar'])
        self.assertTrue('shopperInfo' in doc['data']['domainQuery'])
        self.assertTrue('domainCount' in doc['data']['domainQuery']['shopperInfo'])
        self.assertTrue('shopperCreateDate' in doc['data']['domainQuery']['shopperInfo'])
        self.assertTrue('shopperId' in doc['data']['domainQuery']['shopperInfo'])
        self.assertTrue('customerId' in doc['data']['domainQuery']['shopperInfo'])
        self.assertTrue('shopperPlid' in doc['data']['domainQuery']['shopperInfo'])
        self.assertTrue('vip' in doc['data']['domainQuery']['shopperInfo'])
        self.assertTrue('blacklist' in doc['data']['domainQuery']['shopperInfo']['vip'])
        self.assertTrue('portfolioType' in doc['data']['domainQuery']['shopperInfo']['vip'])
        self.assertTrue('shopperId' in doc['data']['domainQuery']['shopperInfo']['vip'])

    def test_api_cmap_merge(self):
        apidata = {'info': 'apidata'}
        cmapdata = {'data': {'domainQuery': 'cmapdata'}}
        cmapv2data = {'productData': {'product': {}, 'cmapv2data': 'data'}}
        mapped_cmapv2 = {'cmapv2data': 'productData'}
        doc = self.cmapservice.api_cmap_merge(apidata, cmapdata, cmapv2data, mapped_cmapv2)
        self.assertTrue(doc == {'info': 'apidata', 'data': {'domainQuery': 'cmapdata'}, 'productData': {'product': {}, 'cmapv2data': 'data'}, 'cmapv2data': 'productData'})
        apidata = {'info': {'info': 'apidata'}, 'info': 'dupe'}
        cmapdata = {'data': {'domainQuery': 'cmapdata'}, 'domainQuery': ['query']}
        doc2 = self.cmapservice.api_cmap_merge(apidata, cmapdata, cmapv2data, mapped_cmapv2)
        self.assertTrue(doc2 == {'info': 'dupe', 'data': {'domainQuery': 'cmapdata'}, 'domainQuery': ['query'], 'productData': {'product': {}, 'cmapv2data': 'data'}, 'cmapv2data': 'productData'})

        with self.assertRaises(KeyError):
            self.cmapservice.api_cmap_merge(self.cmapservice.api_cmap_merge(apidata, None, cmapv2data, mapped_cmapv2))

    def test_date_time_format(self):
        date = self.cmapservice._date_time_format('2007-03-08T12:11:06Z')
        self.assertTrue(date == parser.parse('2007-03-08 12:11:06'))
        date2 = self.cmapservice._date_time_format('invaliddatetimestring')
        self.assertTrue(date2 is None)

    def test_validate_dq_structure(self):
        test_data = {
            'data': {
                'domainQuery': {
                    'host': {},
                    'registrar': {},
                    'apiReseller': {},
                    'securitySubscription': {},
                    'shopperInfo': {}
                }
            }
        }
        self.assertIsNone(self.cmapservice._validate_dq_structure(test_data))

    def test_validate_dq_structure_missing_field(self):
        test_data = {
            'data': {
                'domainQuery': {
                    'host': {},
                    'registrar': {},
                    'apiReseller': {},
                    'securitySubscription': {}
                }
            }
        }
        self.assertRaises(TypeError, self.cmapservice._validate_dq_structure, test_data)

    def test_validate_dq_structure_missing_dq(self):
        test_data = {
            'data': {
            }
        }
        self.assertRaises(TypeError, self.cmapservice._validate_dq_structure, test_data)

    def test_validate_dq_structure_missing_data(self):
        test_data = {}
        self.assertRaises(TypeError, self.cmapservice._validate_dq_structure, test_data)

    @patch.object(CmapServiceHelper, 'cmap_query')
    def test_product_lookup(self, cmap_query):
        cmap_query.return_value = {'example': 'data'}
        result = self.cmapservice.product_lookup('domain', 'test-guid', 'ip', 'product')
        cmap_query.assert_called_with('{"domain": "domain", "guid": "test-guid", "ip": "ip", "product": "product"}', '/v1/hosted/lookup')
        self.assertDictEqual(result, cmap_query.return_value)

    @patch.object(CmapServiceHelper, 'cmap_query')
    def test_product_lookup_entitlement(self, cmap_query):
        entitlement_data = {'data': 'testData2'}
        cmap_query.return_value = [entitlement_data]
        result = self.cmapservice.product_lookup_entitlement('test_customer', 'test_entitlement')
        cmap_query.assert_called_with('', '/v1/nes/test_customer/test_entitlement')
        self.assertEqual(result, entitlement_data)

    @patch.object(CmapServiceHelper, 'cmap_query')
    def test_shopper_lookup(self, cmap_query):
        cmap_query.return_value = {'example': 'data'}
        result = self.cmapservice.shopper_lookup('shopper')
        cmap_query.assert_called_with('{"shopper_id": "shopper"}', '/v1/shopper/lookup')
        self.assertDictEqual(result, cmap_query.return_value)
