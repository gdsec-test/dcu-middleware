import mongomock
from dcdatabase.mongohelper import MongoHelper
from mock import patch
from nose.tools import assert_true

from dcumiddleware.phishingstrategy import PhishingStrategy
from dcumiddleware.urihelper import URIHelper
from dcumiddleware.cmapservicehelper import CmapServiceHelper
from test_settings import TestingConfig


class TestPhishingStrategy:

    @classmethod
    def setup_class(cls):
        config = TestingConfig()
        cls._phishing = PhishingStrategy(config)
        cls._urihelper = URIHelper(config)
        # Replace underlying db implementation with mock
        cls._phishing._db._mongo._collection = mongomock.MongoClient().db.collection

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    @patch.object(CmapServiceHelper, "api_cmap_merge")
    @patch.object(CmapServiceHelper, "domain_query")
    def test_process_hosted(self, domain_query, api_cmap_merge, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = {'sourceDomainOrIp': u'comicsn.beer',
                       'ticketId': u'DCU000001053',
                       'reporter': u'bxberry',
                       'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
                       'type': u'PHISHING'
                       }
        domain_query.return_value = {"data": {
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
											        "blacklist": None,
											        "PortfolioType": 'No Premium Services For This Shopper'
										        },
										        "child": None
									        },
									        "blacklist": None
								        }
							        }}
        api_cmap_merge.return_value = {'sourceDomainOrIp': u'comicsn.beer',
                       'ticketId': u'DCU000001053',
                       'reporter': u'bxberry',
                       'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
                       'type': u'PHISHING',
                       "data": {
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
								        "blacklist": None,
								        "PortfolioType": 'No Premium Services For This Shopper'
							        },
							        "child": None
						        },
						        "blacklist": None
					        }
				        }
                       }
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001053')
        assert_true(doc['ticketId'] == 'DCU000001053')
        assert_true(doc['hosted_status'] == 'HOSTED')
        assert_true('vip_unconfirmed' not in doc)
        assert_true('blacklist' not in doc)

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    @patch.object(CmapServiceHelper, "api_cmap_merge")
    @patch.object(CmapServiceHelper, "domain_query")
    def test_process_foreign(self, domain_query, api_cmap_merge, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'google.com',
                        'ticketId': u'DCU000001054',
                        'reporter': u'bxberry',
                        'source': u'http://google.com',
                        'type': u'PHISHING'
                        }
        domain_query.return_value = {"data": {
									        "domainQuery": {
										        "host": {
											        "name": "LVLT-ORG-8-8"
										        },
										        "registrar": {
											        "name": "MarkMonitor, Inc.",
											        "createDate": "1997-09-15"
										        },
										        "apiReseller": {
											        "parent": None,
											        "child": None
										        },
										        "shopperInfo": {
											        "shopperId": None,
											        "dateCreated": None,
											        "domainCount": 0,
											        "vip": {
												        "blacklist": None,
												        "PortfolioType": None
											        },
											        "child": None
										        },
										        "blacklist": None
									        }
								    }}
        api_cmap_merge.return_value = {'sourceDomainOrIp': u'google.com',
                                       'ticketId': u'DCU000001054',
                                       'reporter': u'bxberry',
                                       'source': u'http://google.com',
                                       'type': u'PHISHING',
                                       "data": {
	                                       "domainQuery": {
		                                       "host": {
			                                       "name": "LVLT-ORG-8-8"
		                                       },
		                                       "registrar": {
			                                       "name": "MarkMonitor, Inc.",
			                                       "createDate": "1997-09-15"
		                                       },
		                                       "apiReseller": {
			                                       "parent": None,
			                                       "child": None
		                                       },
		                                       "shopperInfo": {
			                                       "shopperId": None,
			                                       "dateCreated": None,
			                                       "domainCount": 0,
			                                       "vip": {
				                                       "blacklist": None,
				                                       "PortfolioType": None
			                                       },
			                                       "child": None
		                                       },
		                                       "blacklist": None
	                                       }
                                       }}
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001054')
        assert_true(doc['ticketId'] == 'DCU000001054')
        assert_true(doc['hosted_status'] == 'FOREIGN')
        assert_true(doc['phishstory_status'] == 'CLOSED')
        assert_true(doc['close_reason'] == 'unworkable')
        assert_true('vip_unconfirmed' not in doc)
        assert_true('blacklist' not in doc)

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    @patch.object(CmapServiceHelper, "api_cmap_merge")
    @patch.object(CmapServiceHelper, "domain_query")
    def test_process_unknown(self, domain_query, api_cmap_merge, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'',
                        'ticketId': u'DCU000001055',
                        'reporter': u'bxberry',
                        'source': u'http://',
                        'type': u'PHISHING'
                        }
        domain_query.return_value = {
	        "data": {
		        "domainQuery": {
			        "host": {
				        "name": None
			        },
			        "registrar": {
				        "name": None,
				        "createDate": None
			        },
			        "apiReseller": {
				        "parent": None,
				        "child": None
			        },
			        "shopperInfo": {
				        "shopperId": None,
				        "dateCreated": None,
				        "domainCount": 0,
				        "vip": {
					        "blacklist": None,
					        "PortfolioType": None
				        },
				        "child": None
			        },
			        "blacklist": None
		        }
	        }
        }
        api_cmap_merge.return_value = {'sourceDomainOrIp': u'',
                                       'ticketId': u'DCU000001055',
                                       'reporter': u'bxberry',
                                       'source': u'http://',
                                       'type': u'PHISHING',
                                       "data": {
	                                       "domainQuery": {
		                                       "host": {
			                                       "name": None
		                                       },
		                                       "registrar": {
			                                       "name": None,
			                                       "createDate": None
		                                       },
		                                       "apiReseller": {
			                                       "parent": None,
			                                       "child": None
		                                       },
		                                       "shopperInfo": {
			                                       "shopperId": None,
			                                       "dateCreated": None,
			                                       "domainCount": 0,
			                                       "vip": {
				                                       "blacklist": None,
				                                       "PortfolioType": None
			                                       },
			                                       "child": None
		                                       },
		                                       "blacklist": None
	                                       }
                                       }
                                       }
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001055')
        assert_true(doc['ticketId'] == 'DCU000001055')
        assert_true(doc['hosted_status'] == 'UNKNOWN')
        assert_true(doc['phishstory_status'] == 'CLOSED')
        assert_true(doc['close_reason'] == 'unworkable')
        assert_true('vip_unconfirmed' not in doc)
        assert_true('blacklist' not in doc)

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    @patch.object(CmapServiceHelper, "api_cmap_merge")
    @patch.object(CmapServiceHelper, "domain_query")
    def test_process_proxy(self, domain_query, api_cmap_merge, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'comicsn.beer',
                        'ticketId': u'DCU000001056',
                        'reporter': u'bxberry',
                        'source': u'http://comicsn.beer',
                        'proxy': u'brazil',
                        'type': u'PHISHING'
                        }
        domain_query.return_value = {"data": {
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
				        "blacklist": None,
				        "PortfolioType": 'No Premium Services For This Shopper'
			        },
			        "child": None
		        },
		        "blacklist": None
	        }
        }}

        api_cmap_merge.return_value = {'sourceDomainOrIp': u'comicsn.beer',
                                       'ticketId': u'DCU000001056',
                                       'reporter': u'bxberry',
                                       'source': u'http://comicsn.beer',
                                       'proxy': u'brazil',
                                       'type': u'PHISHING',
                                       "data": {
	                                       "domainQuery": {
		                                       "host": {
			                                       "hostNetwork": "GO-DADDY-COM-LLC"
		                                       },
		                                       "registrar": {
			                                       "name": "GO-DADDY-COM-LLC"
		                                       },
		                                       "domainCreateDate": {
			                                       "creationDate": "2014/09/25"
		                                       },
		                                       "profile": {
			                                       "Vip": "false"
		                                       },
		                                       "shopperByDomain": {
			                                       "shopperId": "49047180",
			                                       "dateCreated": "1/9/2012 7:41:51 PM",
			                                       "domainCount": 9
		                                       },
		                                       "reseller": {
			                                       "parentChild": "No Parent/Child Info Found"
		                                       }
	                                       }
                                       }
                                       }
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001056')
        assert_true(doc['ticketId'] == 'DCU000001056')
        assert_true(doc['proxy'] == 'brazil')

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    @patch.object(CmapServiceHelper, "api_cmap_merge")
    @patch.object(CmapServiceHelper, "domain_query")
    def test_process_reg(self, domain_query, api_cmap_merge, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'comicsn.beer',
                        'ticketId': u'DCU000001057',
                        'reporter': u'bxberry',
                        'source': u'http://comicsn.beer',
                        'type': u'PHISHING'
                        }
        domain_query.return_value = {"data": {
	        "domainQuery": {
		        "host": {
			        "name": "LVLT-ORG-8-8"
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
				        "blacklist": None,
				        "PortfolioType": 'No Premium Services For This Shopper'
			        },
			        "child": None
		        },
		        "blacklist": None
	        }
        }}

        api_cmap_merge.return_value = {'sourceDomainOrIp': u'comicsn.beer',
                                       'ticketId': u'DCU000001057',
                                       'reporter': u'bxberry',
                                       'source': u'http://comicsn.beer',
                                       'type': u'PHISHING',
                                       "data": {
	                                       "domainQuery": {
		                                       "host": {
			                                       "name": "LVLT-ORG-8-8"
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
				                                       "blacklist": None,
				                                       "PortfolioType": 'No Premium Services For This Shopper'
			                                       },
			                                       "child": None
		                                       },
		                                       "blacklist": None
	                                       }
                                       }
                                       }
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001057')
        assert_true(doc['ticketId'] == 'DCU000001057')
        assert_true(doc['hosted_status'] == 'REGISTERED')
        assert_true('vip_unconfirmed' not in doc)
        assert_true('blacklist' not in doc)

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    @patch.object(CmapServiceHelper, "api_cmap_merge")
    @patch.object(CmapServiceHelper, "domain_query")
    def test_process_vip_blacklist(self, domain_query, api_cmap_merge, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'comicsn.beer',
                        'ticketId': u'DCU000001058',
                        'reporter': u'bxberry',
                        'source': u'http://comicsn.beer',
                        'type': u'PHISHING'
                        }
        domain_query.return_value = {"data": {
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
			        "shopperId": None,
			        "dateCreated": "2012-01-09",
			        "domainCount": 9,
			        "vip": {
				        "blacklist": True,
				        "PortfolioType": 'No Premium Services For This Shopper'
			        },
			        "child": None
		        },
		        "blacklist": True
	        }
        }
        }
        api_cmap_merge.return_value = {'sourceDomainOrIp': u'comicsn.beer',
                                       'ticketId': u'DCU000001058',
                                       'reporter': u'bxberry',
                                       'source': u'http://comicsn.beer',
                                       'type': u'PHISHING',
                                       "data": {
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
			                                       "shopperId": None,
			                                       "dateCreated": "2012-01-09",
			                                       "domainCount": 9,
			                                       "vip": {
				                                       "blacklist": True,
				                                       "PortfolioType": 'No Premium Services For This Shopper'
			                                       },
			                                       "child": None
		                                       },
		                                       "blacklist": True
	                                       }
                                       }
                                       }
        self._phishing.process(test_record)
        doc = self._phishing._db.get_incident('DCU000001058')
        assert_true(doc['ticketId'] == 'DCU000001058')
        assert_true(doc['hosted_status'] == 'HOSTED')
        assert_true(doc['vip_unconfirmed'] is True)
        assert_true(doc['blacklist'] is True)
