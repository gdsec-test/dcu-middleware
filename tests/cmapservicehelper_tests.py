from nose.tools import assert_true
from dcumiddleware.cmapservicehelper import CmapServiceHelper
from test_settings import TestingConfig
from datetime import datetime


class TestCmapServiceHelper:

	def __init__(self):
		config = TestingConfig()
		self.cmapservice = CmapServiceHelper(config)

	def test_domain_query(self):
		domain = "comicsn.beer"
		doc = self.cmapservice.domain_query(domain)
		assert_true(doc['data']['domainQuery']['host']['name'] == 'GO-DADDY-COM-LLC')
		assert_true(doc['data']['domainQuery']['registrar']['name'] == 'GoDaddy.com, LLC')
		assert_true(doc['data']['domainQuery']['registrar']['createDate'] == datetime.strptime('2014-09-25', '%Y-%m-%d'))
		assert_true(doc['data']['domainQuery']['apiReseller']['parent'] is None)
		assert_true(doc['data']['domainQuery']['apiReseller']['child'] is None)
		assert_true(doc['data']['domainQuery']['shopperInfo']['shopperId'] == '49047180')
		assert_true(doc['data']['domainQuery']['shopperInfo']['dateCreated'] == datetime.strptime('2012-01-09', '%Y-%m-%d'))
		assert_true(doc['data']['domainQuery']['shopperInfo']['domainCount'] == 9)
		assert_true(doc['data']['domainQuery']['shopperInfo']['vip']['blacklist'] is True)
		assert_true(
			doc['data']['domainQuery']['shopperInfo']['vip']['PortfolioType'] == 'No Premium Services For This Shopper')
		assert_true(doc['data']['domainQuery']['blacklist'] is True)

	def test_domain_query2(self):
		doc = self.cmapservice.domain_query(None)
		assert_true(doc is None)

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
								"name": "GO-DADDY-COM-LLC"
							},
							"registrar": {
								"name": "GoDaddy.com, LLC",
								"createDate": "2014-09-25"
							},
							"apiReseller": {
								"parent": None,
								"child": None
							},
							"shopperInfo": {
								"shopperId": "49047180",
								"dateCreated": "2012-01-09",
								"domainCount": 9,
								"vip": {
									"blacklist": True,
									"PortfolioType": 'No Premium Services For This Shopper'
								},
							},
							"blacklist": True
						}
					}}
		doc = self.cmapservice.api_cmap_merge(apidata, cmapdata)
		assert_true(doc['data']['domainQuery']['host']['name'] == 'GO-DADDY-COM-LLC')
		assert_true(doc['data']['domainQuery']['registrar']['name'] == 'GoDaddy.com, LLC')
		assert_true(doc['data']['domainQuery']['registrar']['createDate'] == '2014-09-25')
		assert_true(doc['data']['domainQuery']['apiReseller']['parent'] is None)
		assert_true(doc['data']['domainQuery']['apiReseller']['child'] is None)
		assert_true(doc['data']['domainQuery']['shopperInfo']['shopperId'] == '49047180')
		assert_true(doc['data']['domainQuery']['shopperInfo']['dateCreated'] == '2012-01-09')
		assert_true(doc['data']['domainQuery']['shopperInfo']['domainCount'] == 9)
		assert_true(doc['data']['domainQuery']['shopperInfo']['vip']['blacklist'] is True)
		assert_true(
			doc['data']['domainQuery']['shopperInfo']['vip']['PortfolioType'] == 'No Premium Services For This Shopper')
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
		date = self.cmapservice._date_time_format('2012-01-09')
		assert_true(date == datetime.strptime('2012-01-09', '%Y-%m-%d'))
		date2 = self.cmapservice._date_time_format('fail')
		assert_true(date2 == 'fail')
