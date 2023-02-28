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
        apidata = {'info': 'My spam Farm is better than yours...',
                   'target': 'The spam Brothers',
                   'reporter': 'testuser',
                   'source': 'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324',
                   'sourceDomainOrIp': 'spam.com',
                   'proxy': 'Must be viewed from an German IP',
                   'ticketId': 'DCU000001053',
                   'type': 'PHISHING'
                   }
        cmapdata = {'data': {
            'domainQuery': {
                'host': {
                    'hostingCompanyName': 'GO-DADDY-COM-LLC'
                },
                'registrar': {
                    'registrarName': 'GoDaddy.com, LLC',
                    'domainCreateDate': '2014-09-25'
                },
                'apiReseller': {
                    'parent': None,
                    'child': None
                },
                'shopperInfo': {
                    'shopperId': '49047180',
                    'customerId': "1234-5678-9012",
                    'shopperCreateDate': '2012-01-09',
                    'domainCount': 9,
                    'vip': {
                        'blacklist': True,
                        'portfolioType': 'No Premium Services For This Shopper'
                    },
                },
                'blacklist': True
            }
        }}
        doc = self.cmapservice.api_cmap_merge(apidata, cmapdata)
        self.assertTrue(doc['data']['domainQuery']['host']['hostingCompanyName'] == 'GO-DADDY-COM-LLC')
        self.assertTrue(doc['data']['domainQuery']['registrar']['registrarName'] == 'GoDaddy.com, LLC')
        self.assertTrue(doc['data']['domainQuery']['registrar']['domainCreateDate'] == '2014-09-25')
        self.assertTrue(doc['data']['domainQuery']['apiReseller']['parent'] is None)
        self.assertTrue(doc['data']['domainQuery']['apiReseller']['child'] is None)
        self.assertTrue(doc['data']['domainQuery']['shopperInfo']['shopperId'] == '49047180')
        self.assertEqual(doc['data']['domainQuery']['shopperInfo']['customerId'], "1234-5678-9012")
        self.assertTrue(doc['data']['domainQuery']['shopperInfo']['shopperCreateDate'] == '2012-01-09')
        self.assertTrue(doc['data']['domainQuery']['shopperInfo']['domainCount'] == 9)
        self.assertTrue(doc['data']['domainQuery']['shopperInfo']['vip']['blacklist'] is True)
        self.assertTrue(
            doc['data']['domainQuery']['shopperInfo']['vip']['portfolioType'] == 'No Premium Services For This Shopper')
        self.assertTrue(doc['data']['domainQuery']['blacklist'] is True)
        self.assertTrue(doc['info'] == 'My spam Farm is better than yours...')
        self.assertTrue(doc['target'] == 'The spam Brothers')
        self.assertTrue(doc['reporter'] == 'testuser')
        self.assertTrue(doc['source'] == 'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324')
        self.assertTrue(doc['sourceDomainOrIp'] == 'spam.com')
        self.assertTrue(doc['proxy'] == 'Must be viewed from an German IP')
        self.assertTrue(doc['ticketId'] == 'DCU000001053')
        self.assertTrue(doc['type'] == 'PHISHING')
        doc2 = self.cmapservice.api_cmap_merge(apidata, None)
        self.assertTrue(doc2['type'] == 'PHISHING')

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
