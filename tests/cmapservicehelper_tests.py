import mongomock
from mock import patch
from nose.tools import assert_true
from dcumiddleware.cmapservicehelper import CmapServiceHelper


class TestCmapServiceHelper:

	def __init__(self):
		self.cmapservice = CmapServiceHelper()

	def test_domain_query(self):
		domain = "comicsn.beer"
		doc = self.cmapservice.domain_query(domain)
		assert_true(doc['data']['domainQuery']['profile']['Vip'] == 'false')
		assert_true(doc['data']['domainQuery']['reseller']['parentChild'] == 'No Parent/Child Info Found')
		assert_true(doc['data']['domainQuery']['shopperByDomain']['domainCount'] == 9)
		assert_true(doc['data']['domainQuery']['shopperByDomain']['shopperId'] == '49047180')
		assert_true(doc['data']['domainQuery']['shopperByDomain']['dateCreated'] == '1/9/2012 7:41:51 PM')
		assert_true(doc['data']['domainQuery']['host']['hostNetwork'] == 'GO-DADDY-COM-LLC')
		assert_true(doc['data']['domainQuery']['domainCreateDate']['creationDate'] == '2014/09/25')
		assert_true(doc['data']['domainQuery']['registrar']['name'] is None)

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
		                    'profile': {
			                    'Vip': u'false'
		                    },
		                    'reseller': {
			                    'parentChild': u'No Parent/Child Info Found'
		                    },
		                    'shopperByDomain': {
			                    'domainCount': 9,
			                    'shopperId': u'49047180',
			                    'dateCreated': u'1/9/2012 7:41:51 PM'
		                    },
		                    'host': {
			                    'hostNetwork': u'GO-DADDY-COM-LLC'
		                    },
		                    'domainCreateDate': {
			                    'creationDate': u'2014/09/25'
		                    },
		                    'registrar': {
			                    'name': None
		                    }
	                    }
                    }
					}
		doc = self.cmapservice.api_cmap_merge(apidata, cmapdata)
		assert_true(doc['data']['domainQuery']['profile']['Vip'] == 'false')
		assert_true(doc['data']['domainQuery']['reseller']['parentChild'] == 'No Parent/Child Info Found')
		assert_true(doc['data']['domainQuery']['shopperByDomain']['domainCount'] == 9)
		assert_true(doc['data']['domainQuery']['shopperByDomain']['shopperId'] == '49047180')
		assert_true(doc['data']['domainQuery']['shopperByDomain']['dateCreated'] == '1/9/2012 7:41:51 PM')
		assert_true(doc['data']['domainQuery']['host']['hostNetwork'] == 'GO-DADDY-COM-LLC')
		assert_true(doc['data']['domainQuery']['domainCreateDate']['creationDate'] == '2014/09/25')
		assert_true(doc['data']['domainQuery']['registrar']['name'] is None)
		assert_true(doc['info'] == 'My spam Farm is better than yours...')
		assert_true(doc['target'] == 'The spam Brothers')
		assert_true(doc['reporter'] == 'bxberry')
		assert_true(doc['source'] == 'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324')
		assert_true(doc['sourceDomainOrIp'] == 'spam.com')
		assert_true(doc['proxy'] == 'Must be viewed from an German IP')
		assert_true(doc['ticketId'] == 'DCU000001053')
		assert_true(doc['type'] == 'PHISHING')
