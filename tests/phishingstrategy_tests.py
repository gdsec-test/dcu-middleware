import mongomock
from dcdatabase.mongohelper import MongoHelper
from mock import patch
from nose.tools import assert_true

from dcumiddleware.phishingstrategy import PhishingStrategy
from dcumiddleware.urihelper import URIHelper
from test_settings import TestingConfig
from datetime import datetime


"""
Sample Graphine data:
{
  "data": {
    "domainQuery": {
      "domain": "comicsn.beer",
      "registrar": {
        "name": "None",
        "parentChild": null
      },
      "reseller": {
        "name": null,
        "parentChild": "No Parent/Child Info Found",
        "abuseContact": null
      },
      "shopperByDomain": {
        "shopperId": "49047180",
        "dateCreated": "1/9/2012 7:41:51 PM",
        "child": null,
        "domainCount": 9,
        "domainsearch": {
          "results": []
        },
        "firstName": "Patrick",
        "email": "outlawgames@gmail.com",
        "domain": "comicsn.beer",
        "othershopperlist": [
          {
            "shopperId": "54459007",
            "dateCreated": "7/20/2012 3:00:30 PM",
            "child": null,
            "domainCount": 0,
            "firstName": "Patrick",
            "email": "pmcconnell@secureserver.net"
          }
        ]
      },
      "profile": {
        "Vip": "false"
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
    def test_process_hosted(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = {'sourceDomainOrIp': u'comicsn.beer',
                       'ticketId': u'DCU000001053',
                       'reporter': u'bxberry',
                       'source': u'http://comicsn.beer/uncategorized/casual-gaming-and-the-holidays/',
                       'type': u'PHISHING',
                       "data": {
	                       "domainQuery": {
		                       "domain": "comicsn.beer",
		                       "host": {
			                       "name": "Go Daddy, LLC",
		                       },
		                       "dateCreated": "1/9/2012 7:41:51 PM",
		                       "registrar": {
			                       "name": "None",
			                       "parentChild": None
		                       },
		                       "reseller": {
			                       "name": None,
			                       "parentChild": "No Parent/Child Info Found",
			                       "abuseContact": None
		                       },
		                       "shopperByDomain": {
			                       "shopperId": "49047180",
			                       "dateCreated": "1/9/2012 7:41:51 PM",
			                       "child": None,
			                       "domainCount": 9,
			                       "domainsearch": {
				                       "results": []
			                       },
			                       "firstName": "Patrick",
			                       "email": "outlawgames@gmail.com",
			                       "domain": "comicsn.beer",
			                       "othershopperlist": [
				                       {
					                       "shopperId": "54459007",
					                       "dateCreated": "7/20/2012 3:00:30 PM",
					                       "child": None,
					                       "domainCount": 0,
					                       "firstName": "Patrick",
					                       "email": "pmcconnell@secureserver.net"
				                       }
			                       ]
		                       },
		                       "profile": {
			                       "Vip": "false"
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
    def test_process_foreign(self, uri_method, mongo_method):
        uri_method.return_value = (1,1)
        mongo_method.return_value = '1'
        test_record = { 'sourceDomainOrIp': u'google.com',
                        'ticketId': u'DCU000001054',
                        'reporter': u'bxberry',
                        'source': u'http://google.com',
                        'type': u'PHISHING',
                        "data": {
				            "domainQuery": {
					            "domain": "google.com",
					            "host": {
						            "name": "Google Inc.",
					            },
					            "dateCreated": "1/9/2012 7:41:51 PM",
					            "registrar": {
						            "name": "MarkMonitor, Inc.",
						            "parentChild": None
					            },
					            "reseller": {
						            "name": None,
						            "parentChild": "No Parent/Child Info Found",
						            "abuseContact": None
					            },
					            "shopperByDomain": {
						            "shopperId": "49047180",
						            "dateCreated": "1/9/2012 7:41:51 PM",
						            "child": None,
						            "domainCount": 9,
						            "domainsearch": {
							            "results": []
						            },
						            "firstName": "Patrick",
						            "email": "outlawgames@gmail.com",
						            "domain": "comicsn.beer",
						            "othershopperlist": [
							            {
								            "shopperId": "54459007",
								            "dateCreated": "7/20/2012 3:00:30 PM",
								            "child": None,
								            "domainCount": 0,
								            "firstName": "Patrick",
								            "email": "pmcconnell@secureserver.net"
							            }
						            ]
					            },
					            "profile": {
						            "Vip": "false"
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

    # @patch.object(MongoHelper, "save_file")
    # @patch.object(URIHelper, "get_site_data")
    # def test_process_unknown(self, uri_method, mongo_method):
    #     uri_method.return_value = (1,1)
    #     mongo_method.return_value = '1'
    #     test_record = { 'sourceDomainOrIp': u'',
    #                     'ticketId': u'DCU000001055',
    #                     'reporter': u'bxberry',
    #                     'source': u'http://',
    #                     'type': u'PHISHING',
    #                     "data": {
		# 		            "domainQuery": {
		# 			            "domain": "",
		# 			            "host": {
		# 				            "name": "",
		# 			            },
		# 			            "dateCreated": "1/9/2012 7:41:51 PM",
		# 			            "registrar": {
		# 				            "name": "",
		# 				            "parentChild": None
		# 			            },
		# 			            "reseller": {
		# 				            "name": None,
		# 				            "parentChild": "No Parent/Child Info Found",
		# 				            "abuseContact": None
		# 			            },
		# 			            "shopperByDomain": {
		# 				            "shopperId": "49047180",
		# 				            "dateCreated": "1/9/2012 7:41:51 PM",
		# 				            "child": None,
		# 				            "domainCount": 9,
		# 				            "domainsearch": {
		# 					            "results": []
		# 				            },
		# 				            "firstName": "Patrick",
		# 				            "email": "outlawgames@gmail.com",
		# 				            "domain": "comicsn.beer",
		# 				            "othershopperlist": [
		# 					            {
		# 						            "shopperId": "54459007",
		# 						            "dateCreated": "7/20/2012 3:00:30 PM",
		# 						            "child": None,
		# 						            "domainCount": 0,
		# 						            "firstName": "Patrick",
		# 						            "email": "pmcconnell@secureserver.net"
		# 					            }
		# 				            ]
		# 			            },
		# 			            "profile": {
		# 				            "Vip": "false"
		# 			            }
		# 		            }
		# 	            }
    #                     }
    #     self._phishing.process(test_record)
    #     doc = self._phishing._db.get_incident('DCU000001055')
    #     assert_true(doc['ticketId'] == 'DCU000001055')
    #     assert_true(doc['hosted_status'] == 'UNKNOWN')
    #     assert_true(doc['phishstory_status'] == 'CLOSED')
    #     assert_true(doc['close_reason'] == 'unworkable')

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
						        "domain": "",
						        "host": {
							        "name": "",
						        },
						        "dateCreated": "1/9/2012 7:41:51 PM",
						        "registrar": {
							        "name": "",
							        "parentChild": None
						        },
						        "reseller": {
							        "name": None,
							        "parentChild": "No Parent/Child Info Found",
							        "abuseContact": None
						        },
						        "shopperByDomain": {
							        "shopperId": "49047180",
							        "dateCreated": "1/9/2012 7:41:51 PM",
							        "child": None,
							        "domainCount": 9,
							        "domainsearch": {
								        "results": []
							        },
							        "firstName": "Patrick",
							        "email": "outlawgames@gmail.com",
							        "domain": "comicsn.beer",
							        "othershopperlist": [
								        {
									        "shopperId": "54459007",
									        "dateCreated": "7/20/2012 3:00:30 PM",
									        "child": None,
									        "domainCount": 0,
									        "firstName": "Patrick",
									        "email": "pmcconnell@secureserver.net"
								        }
							        ]
						        },
						        "profile": {
							        "Vip": "false"
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
		                        "domain": "sapphires3.com",
		                        "host": {
			                        "name": "Google, LLC",
		                        },
		                        "dateCreated": "1/9/2012 7:41:51 PM",
		                        "registrar": {
			                        "name": "Go Daddy, LLC",
			                        "parentChild": None
		                        },
		                        "reseller": {
			                        "name": None,
			                        "parentChild": "No Parent/Child Info Found",
			                        "abuseContact": None
		                        },
		                        "shopperByDomain": {
			                        "shopperId": "49047180",
			                        "dateCreated": "1/9/2012 7:41:51 PM",
			                        "child": None,
			                        "domainCount": 9,
			                        "domainsearch": {
				                        "results": []
			                        },
			                        "firstName": "Patrick",
			                        "email": "outlawgames@gmail.com",
			                        "domain": "comicsn.beer",
			                        "othershopperlist": [
				                        {
					                        "shopperId": "54459007",
					                        "dateCreated": "7/20/2012 3:00:30 PM",
					                        "child": None,
					                        "domainCount": 0,
					                        "firstName": "Patrick",
					                        "email": "pmcconnell@secureserver.net"
				                        }
			                        ]
		                        },
		                        "profile": {
			                        "Vip": "false"
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
