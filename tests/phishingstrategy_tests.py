import mongomock
from dcdatabase.mongohelper import MongoHelper
from mock import patch
from nose.tools import assert_true

from dcumiddleware.phishingstrategy import PhishingStrategy
from dcumiddleware.urihelper import URIHelper
from dcumiddleware.cmapservicehelper import GrapheneAccess
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
    @patch.object(GrapheneAccess, "api_cmap_merge")
    @patch.object(GrapheneAccess, "domain_query")
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
        api_cmap_merge.return_value = {'sourceDomainOrIp': u'comicsn.beer',
                       'ticketId': u'DCU000001053',
                       'reporter': u'bxberry',
                       'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
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
        doc = self._phishing._db.get_incident('DCU000001053')
        assert_true(doc['ticketId'] == 'DCU000001053')
        assert_true(doc['hosted_status'] == 'HOSTED')

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    @patch.object(GrapheneAccess, "api_cmap_merge")
    @patch.object(GrapheneAccess, "domain_query")
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
			        "hostNetwork": "GOOGLE-LLC"
		        },
		        "registrar": {
			        "name": "Mark Monitor"
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
        api_cmap_merge.return_value = {'sourceDomainOrIp': u'google.com',
                                       'ticketId': u'DCU000001054',
                                       'reporter': u'bxberry',
                                       'source': u'http://google.com',
                                       'type': u'PHISHING',
                                       "data": {
	                                       "domainQuery": {
		                                       "host": {
			                                       "hostNetwork": "GOOGLE-LLC"
		                                       },
		                                       "registrar": {
			                                       "name": "Mark Monitor"
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
        doc = self._phishing._db.get_incident('DCU000001054')
        assert_true(doc['ticketId'] == 'DCU000001054')
        assert_true(doc['hosted_status'] == 'FOREIGN')
        assert_true(doc['phishstory_status'] == 'CLOSED')
        assert_true(doc['close_reason'] == 'unworkable')

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    def test_process_unknown(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'',
                        'ticketId': u'DCU000001055',
                        'reporter': u'bxberry',
                        'source': u'http://',
                        'type': u'PHISHING',
                        "data": {
	                        "domainQuery": {
		                        "host": {
			                        "hostNetwork": ""
		                        },
		                        "registrar": {
			                        "name": "None"
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
        doc = self._phishing._db.get_incident('DCU000001055')
        assert_true(doc['ticketId'] == 'DCU000001055')
        assert_true(doc['hosted_status'] == 'UNKNOWN')
        assert_true(doc['phishstory_status'] == 'CLOSED')
        assert_true(doc['close_reason'] == 'unworkable')

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    def test_process_proxy(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'comicsn.beer',
                        'ticketId': u'DCU000001056',
                        'reporter': u'bxberry',
                        'source': u'http://',
                        'proxy': 'brazil',
                        'type': u'PHISHING',
                        "data": {
	                        "domainQuery": {
		                        "host": {
			                        "hostNetwork": "GO-DADDY-COM-LLC"
		                        },
		                        "registrar": {
			                        "name": "None"
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

    @patch.object(MongoHelper, "save_file")
    @patch.object(URIHelper, "get_site_data")
    def test_process_reg(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'sapphires3.com',
                        'ticketId': u'DCU000001057',
                        'reporter': u'bxberry',
                        'source': u'http://sapphires3.com',
                        'type': u'PHISHING',
                        "data": {
	                        "domainQuery": {
		                        "host": {
			                        "hostNetwork": "GOOGLE-LLC"
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
        doc = self._phishing._db.get_incident('DCU000001057')
        assert_true(doc['ticketId'] == 'DCU000001057')
        assert_true(doc['hosted_status'] == 'REGISTERED')
        assert_true(doc['d_create_date'] == '1/9/2012 7:41:51 PM')

    # @patch.object(MongoHelper, "save_file")
    # @patch.object(URIHelper, "get_site_data")
    # def test_process_hosted(self, uri_method, mongo_method):
    #     uri_method.return_value = (1,1)
    #     mongo_method.return_value = '1'
    #     test_record = { 'sourceDomainOrIp': u'comicsn.beer',
    #                     'ticketId': u'DCU000001053',
    #                     'reporter': u'bxberry',
    #                     'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
    #                     'type': u'PHISHING'}
    #     self._phishing.process(test_record)
    #     doc = self._phishing._db.get_incident('DCU000001053')
    #     assert_true(doc['ticketId'] == 'DCU000001053')
    #     assert_true(doc['hosted_status'] == 'HOSTED')
    #
    # @patch.object(MongoHelper, "save_file")
    # @patch.object(URIHelper, "get_site_data")
    # def test_process_foreign(self, uri_method, mongo_method):
    #     uri_method.return_value = (1,1)
    #     mongo_method.return_value = '1'
    #     test_record = { 'sourceDomainOrIp': u'google.com',
    #                     'ticketId': u'DCU000001054',
    #                     'reporter': u'bxberry',
    #                     'source': u'http://google.com',
    #                     'type': u'PHISHING'}
    #     self._phishing.process(test_record)
    #     doc = self._phishing._db.get_incident('DCU000001054')
    #     assert_true(doc['ticketId'] == 'DCU000001054')
    #     assert_true(doc['hosted_status'] == 'FOREIGN')
    #     assert_true(doc['phishstory_status'] == 'CLOSED')
    #     assert_true(doc['close_reason'] == 'unworkable')
    #
    # @patch.object(MongoHelper, "save_file")
    # @patch.object(URIHelper, "get_site_data")
    # def test_process_unknown(self, uri_method, mongo_method):
    #     uri_method.return_value = (1,1)
    #     mongo_method.return_value = '1'
    #     test_record = { 'sourceDomainOrIp': u'',
    #                     'ticketId': u'DCU000001055',
    #                     'reporter': u'bxberry',
    #                     'source': u'http://',
    #                     'type': u'PHISHING'}
    #     self._phishing.process(test_record)
    #     doc = self._phishing._db.get_incident('DCU000001055')
    #     assert_true(doc['ticketId'] == 'DCU000001055')
    #     assert_true(doc['hosted_status'] == 'UNKNOWN')
    #     assert_true(doc['phishstory_status'] == 'CLOSED')
    #     assert_true(doc['close_reason'] == 'unworkable')
    #
    # @patch.object(MongoHelper, "save_file")
    # @patch.object(URIHelper, "get_site_data")
    # def test_process_proxy(self, uri_method, mongo_method):
    #     uri_method.return_value = (1,1)
    #     mongo_method.return_value = '1'
    #     test_record = { 'sourceDomainOrIp': u'comicsn.beer',
    #                     'ticketId': u'DCU000001056',
    #                     'reporter': u'bxberry',
    #                     'source': u'http://',
    #                     'proxy': 'brazil',
    #                     'type': u'PHISHING'}
    #     self._phishing.process(test_record)
    #     doc = self._phishing._db.get_incident('DCU000001056')
    #     assert_true(doc['ticketId'] == 'DCU000001056')
    #
    # @patch.object(MongoHelper, "save_file")
    # @patch.object(URIHelper, "get_site_data")
    # @patch.object(URIHelper, "get_status")
    # def test_process_reg(self, get_status, uri_method, mongo_method):
    #     uri_method.return_value = (1,1)
    #     mongo_method.return_value = '1'
    #     get_status.return_value = (2, datetime.strptime('2014-09-25 16:00:13', '%Y-%m-%d %H:%M:%S'))
    #     test_record = { 'sourceDomainOrIp': u'sapphires3.com',
    #                     'ticketId': u'DCU000001057',
    #                     'reporter': u'bxberry',
    #                     'source': u'http://sapphires3.com',
    #                     'type': u'PHISHING'}
    #     self._phishing.process(test_record)
    #     doc = self._phishing._db.get_incident('DCU000001057')
    #     assert_true(doc['ticketId'] == 'DCU000001057')
    #     assert_true(doc['hosted_status'] == 'REGISTERED')
    #     assert_true(doc['d_create_date'] == datetime.strptime('2014-09-25 16:00:13', '%Y-%m-%d %H:%M:%S'))


"""
Sample Graphine data:
{
  "data": {
    "domainQuery": {
      "host": {
        "hostNetwork": "GO-DADDY-COM-LLC"
      },
      "registrar": {
        "name": null
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
"""

"""
Sample Mongo data:
{
    "_id" : "DCU000001025",
    "source" : "http://inc-apple-id-887698123-verification2016-ios.productostrazzo.com/home/index.html",
    "sourceDomainOrIp" : "productostrazzo.com",
    "created" : ISODate("2016-05-31T14:34:46.611Z"),
    "target" : "Apple ID",
    "reporter" : "129092584",
    "phishstory_status" : "CLOSED",
    "ticketId" : "DCU000001025",
    "type" : "PHISHING",
    "hosted_status" : "HOSTED",
    "sourcecode_id" : ObjectId("574da10c3e8295001836b04d"),
    "last_modified" : ISODate("2016-05-31T14:34:52.945Z"),
    "screenshot_id" : ObjectId("574da10c3e8295001836b04b"),
    "close_reason" : "resolved",
    "closed" : ISODate("2016-06-02T16:52:44.170Z")
}
"""

"""
Sample API data:
{'info': u'My spam Farm is better than yours...',
 'sourceDomainOrIp': u'spam.com',
 'ticketId': u'DCU000001053',
 'target': u'The spam Brothers',
 'reporter': u'bxberry',
 'source': u'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324',
 'proxy': u'Must be viewed from an German IP',
 'type': u'PHISHING'}
"""
