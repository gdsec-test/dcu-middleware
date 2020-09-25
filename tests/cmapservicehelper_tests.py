from dateutil import parser
from mock import patch
from nose.tools import assert_true

from dcumiddleware.cmapservicehelper import CmapServiceHelper
from test_settings import TestingConfig


class TestCmapServiceHelper:
    def __init__(self):
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
                    'domain': 'impcat.com',
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
                        'vip': {
                            'blacklist': False,
                            'portfolioType': None,
                            'shopperId': None
                        }
                    }
                }
            }
        }
        domain = 'impcat.com'
        doc = self.cmapservice.domain_query(domain)
        assert_true('data' in doc)
        assert_true('domainQuery' in doc['data'])
        assert_true('alexaRank' in doc['data']['domainQuery'])
        assert_true('apiReseller' in doc['data']['domainQuery'])
        assert_true('child' in doc['data']['domainQuery']['apiReseller'])
        assert_true('parent' in doc['data']['domainQuery']['apiReseller'])
        assert_true('blacklist' in doc['data']['domainQuery'])
        assert_true('domain' in doc['data']['domainQuery'])
        assert_true('securitySubscription' in doc['data']['domainQuery'])
        assert_true('sslSubscriptions' in doc['data']['domainQuery'])
        assert_true('certCommonName' in doc['data']['domainQuery']['sslSubscriptions'])
        assert_true('certType' in doc['data']['domainQuery']['sslSubscriptions'])
        assert_true('createdAt' in doc['data']['domainQuery']['sslSubscriptions'])
        assert_true('expiresAt' in doc['data']['domainQuery']['sslSubscriptions'])
        assert_true('host' in doc['data']['domainQuery'])
        assert_true('dataCenter' in doc['data']['domainQuery']['host'])
        assert_true('guid' in doc['data']['domainQuery']['host'])
        assert_true('containerId' in doc['data']['domainQuery']['host'])
        assert_true('hostingCompanyName' in doc['data']['domainQuery']['host'])
        assert_true('hostingAbuseEmail' in doc['data']['domainQuery']['host'])
        assert_true('hostname' in doc['data']['domainQuery']['host'])
        assert_true('ip' in doc['data']['domainQuery']['host'])
        assert_true('os' in doc['data']['domainQuery']['host'])
        assert_true('product' in doc['data']['domainQuery']['host'])
        assert_true('shopperId' in doc['data']['domainQuery']['host'])
        assert_true('privateLabelId' in doc['data']['domainQuery']['host'])
        assert_true('vip' in doc['data']['domainQuery']['host'])
        assert_true('blacklist' in doc['data']['domainQuery']['host']['vip'])
        assert_true('portfolioType' in doc['data']['domainQuery']['host']['vip'])
        assert_true('shopperId' in doc['data']['domainQuery']['host']['vip'])
        assert_true('registrar' in doc['data']['domainQuery'])
        assert_true('domainCreateDate' in doc['data']['domainQuery']['registrar'])
        assert_true('registrarAbuseEmail' in doc['data']['domainQuery']['registrar'])
        assert_true('registrarName' in doc['data']['domainQuery']['registrar'])
        assert_true('shopperInfo' in doc['data']['domainQuery'])
        assert_true('domainCount' in doc['data']['domainQuery']['shopperInfo'])
        assert_true('shopperCreateDate' in doc['data']['domainQuery']['shopperInfo'])
        assert_true('shopperId' in doc['data']['domainQuery']['shopperInfo'])
        assert_true('vip' in doc['data']['domainQuery']['shopperInfo'])
        assert_true('blacklist' in doc['data']['domainQuery']['shopperInfo']['vip'])
        assert_true('portfolioType' in doc['data']['domainQuery']['shopperInfo']['vip'])
        assert_true('shopperId' in doc['data']['domainQuery']['shopperInfo']['vip'])

    def test_api_cmap_merge(self):
        apidata = {'info': u'My spam Farm is better than yours...',
                   'target': u'The spam Brothers',
                   'reporter': u'bxberry',
                   'source': u'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324',
                   'sourceDomainOrIp': u'spam.com',
                   'proxy': u'Must be viewed from an German IP',
                   'ticketId': u'DCU000001053',
                   'type': u'PHISHING'
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
        assert_true(doc['data']['domainQuery']['host']['hostingCompanyName'] == 'GO-DADDY-COM-LLC')
        assert_true(doc['data']['domainQuery']['registrar']['registrarName'] == 'GoDaddy.com, LLC')
        assert_true(doc['data']['domainQuery']['registrar']['domainCreateDate'] == '2014-09-25')
        assert_true(doc['data']['domainQuery']['apiReseller']['parent'] is None)
        assert_true(doc['data']['domainQuery']['apiReseller']['child'] is None)
        assert_true(doc['data']['domainQuery']['shopperInfo']['shopperId'] == '49047180')
        assert_true(doc['data']['domainQuery']['shopperInfo']['shopperCreateDate'] == '2012-01-09')
        assert_true(doc['data']['domainQuery']['shopperInfo']['domainCount'] == 9)
        assert_true(doc['data']['domainQuery']['shopperInfo']['vip']['blacklist'] is True)
        assert_true(
            doc['data']['domainQuery']['shopperInfo']['vip']['portfolioType'] == 'No Premium Services For This Shopper')
        assert_true(doc['data']['domainQuery']['blacklist'] is True)
        assert_true(doc['info'] == 'My spam Farm is better than yours...')
        assert_true(doc['target'] == 'The spam Brothers')
        assert_true(doc['reporter'] == 'bxberry')
        assert_true(doc['source'] == 'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324')
        assert_true(doc['sourceDomainOrIp'] == 'spam.com')
        assert_true(doc['proxy'] == 'Must be viewed from an German IP')
        assert_true(doc['ticketId'] == 'DCU000001053')
        assert_true(doc['type'] == 'PHISHING')
        doc2 = self.cmapservice.api_cmap_merge(apidata, None)
        assert_true(doc2['type'] == 'PHISHING')

    def test_date_time_format(self):
        date = self.cmapservice._date_time_format('2007-03-08T12:11:06Z')
        assert_true(date == parser.parse('2007-03-08 12:11:06'))
        date2 = self.cmapservice._date_time_format('invaliddatetimestring')
        assert_true(date2 is None)
