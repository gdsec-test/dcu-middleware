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
            "data": {
                "domainQuery": {
                    "alexaRank": 999999,
                    "apiReseller": {
                        "child": None,
                        "parent": None
                    },
                    "blacklist": False,
                    "domain": "impcat.com",
                    "host": {
                        "dataCenter": "Unable to locate",
                        "guid": "c0799e2a-e7f5-11e5-be04-14feb5d40a06",
                        "hostingCompanyName": "GoDaddy.com LLC",
                        "hostingAbuseEmail": [
                            "abuse@godaddy.com"
                        ],
                        "hostname": "Unable to locate",
                        "ip": "184.168.47.225",
                        "os": "Linux",
                        "product": "wpaas",
                        "shopperId": "9sd",
                        "vip": {
                            "blacklist": False,
                            "portfolioType": "No Premium Services For This Shopper",
                            "shopperId": None
                        }
                    },
                    "registrar": {
                        "domainCreateDate": "2009-12-05",
                        "registrarAbuseEmail": [
                            "abuse@godaddy.com"
                        ],
                        "registrarName": "GoDaddy.com, LLC"
                    },
                    "shopperInfo": {
                        "domainCount": 9,
                        "shopperCreateDate": "2003-01-19",
                        "shopperId": "1488039",
                        "vip": {
                            "blacklist": False,
                            "portfolioType": "No Premium Services For This Shopper",
                            "shopperId": None
                        }
                    }
                }
            }
        }
        domain = "impcat.com"
        doc = self.cmapservice.domain_query(domain)
        assert_true(doc['data']['domainQuery']['alexaRank'] == 999999)
        assert_true(doc['data']['domainQuery']['apiReseller']['parent'] is None)
        assert_true(doc['data']['domainQuery']['apiReseller']['child'] is None)
        assert_true(doc['data']['domainQuery']['blacklist'] is False)
        assert_true(doc['data']['domainQuery']['domain'] == "impcat.com")

        assert_true(doc['data']['domainQuery']['host']['dataCenter'] == "Unable to locate")
        assert_true(doc['data']['domainQuery']['host']['guid'] == 'c0799e2a-e7f5-11e5-be04-14feb5d40a06')
        assert_true(doc['data']['domainQuery']['host']['hostingCompanyName'] == 'GoDaddy.com LLC')
        assert_true(doc['data']['domainQuery']['host']['hostingAbuseEmail'] == ['abuse@godaddy.com'])
        assert_true(doc['data']['domainQuery']['host']['hostname'] == 'Unable to locate')

        assert_true(doc['data']['domainQuery']['host']['ip'] == '184.168.47.225')
        assert_true(doc['data']['domainQuery']['host']['os'] == 'Linux')
        assert_true(doc['data']['domainQuery']['host']['product'] == 'wpaas')
        assert_true(doc['data']['domainQuery']['host']['shopperId'] == '9sd')
        assert_true(doc['data']['domainQuery']['host']['vip']['blacklist'] is False)
        assert_true(
            doc['data']['domainQuery']['host']['vip']['portfolioType'] == 'No Premium Services For This Shopper')
        assert_true(doc['data']['domainQuery']['host']['vip']['shopperId'] is None)
        assert_true(doc['data']['domainQuery']['registrar']['domainCreateDate'].isoformat() == '2009-12-05T00:00:00')
        assert_true(doc['data']['domainQuery']['registrar']['registrarAbuseEmail'] == ['abuse@godaddy.com'])
        assert_true(doc['data']['domainQuery']['registrar']['registrarName'] == 'GoDaddy.com, LLC')

        assert_true(doc['data']['domainQuery']['shopperInfo']['domainCount'] == 9)
        assert_true(doc['data']['domainQuery']['shopperInfo']['shopperCreateDate'].isoformat() == '2003-01-19T00:00:00')
        assert_true(doc['data']['domainQuery']['shopperInfo']['shopperId'] == '1488039')
        assert_true(doc['data']['domainQuery']['shopperInfo']['vip']['blacklist'] is False)
        assert_true(
            doc['data']['domainQuery']['shopperInfo']['vip']['portfolioType'] == 'No Premium Services For This Shopper')
        assert_true(doc['data']['domainQuery']['shopperInfo']['vip']['shopperId'] is None)

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
        cmapdata = {"data": {
            "domainQuery": {
                "host": {
                    "hostingCompanyName": "GO-DADDY-COM-LLC"
                },
                "registrar": {
                    "registrarName": "GoDaddy.com, LLC",
                    "domainCreateDate": "2014-09-25"
                },
                "apiReseller": {
                    "parent": None,
                    "child": None
                },
                "shopperInfo": {
                    "shopperId": "49047180",
                    "shopperCreateDate": "2012-01-09",
                    "domainCount": 9,
                    "vip": {
                        "blacklist": True,
                        "portfolioType": 'No Premium Services For This Shopper'
                    },
                },
                "blacklist": True
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
