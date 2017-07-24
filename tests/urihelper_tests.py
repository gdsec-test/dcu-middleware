import logging
from datetime import datetime

import mongomock
from mock import patch
from nose.tools import assert_true, assert_equal, assert_false

from dcumiddleware.urihelper import URIHelper
from whois import NICClient
from test_settings import TestingConfig

WHOIS_DATA = '''
Domain Name: COMICSN.BEER
Registry Domain ID: 68841_MMd1-BEER
Registrar WHOIS Server:
Registrar URL:
Updated Date: 2016-09-26T15:03:22Z
Creation Date: 2014-09-25T16:00:13Z
Registry Expiry Date: 2017-09-25T16:00:13Z
Registrar: GoMontenegro
Registrar IANA ID: 1152
Registrar Abuse Contact Email: tho@godaddy.com
Domain Status: CLIENT DELETE PROHIBITED https://icann.org/epp#clientDeleteProhibited
Domain Status: CLIENT RENEW PROHIBITED https://icann.org/epp#clientRenewProhibited
Domain Status: CLIENT TRANSFER PROHIBITED https://icann.org/epp#clientTransferProhibited
Domain Status: CLIENT UPDATE PROHIBITED https://icann.org/epp#clientUpdateProhibited
Registry Registrant ID: 72138_MMd1-BEER
Registrant Name: Registration Private
Registrant Organization: Domains By Proxy, LLC
Registrant Street: DomainsByProxy.com
Registrant Street: 14455 N. Hayden Road
Registrant City: Scottsdale
Registrant State/Province: Arizona
Registrant Postal Code: 85260
Registrant Country: US
Registrant Phone: +1.4806242599
Registrant Fax: +1.4806242598
Registrant Email: comicsn.beer@domainsbyproxy.com
Registry Admin ID: 72141_MMd1-BEER
Admin Name: Registration Private
Admin Organization: Domains By Proxy, LLC
Admin Street: DomainsByProxy.com
Admin Street: 14455 N. Hayden Road
Admin City: Scottsdale
Admin State/Province: Arizona
Admin Postal Code: 85260
Admin Country: US
Admin Phone: +1.4806242599
Admin Fax: +1.4806242598
Admin Email: comicsn.beer@domainsbyproxy.com
Registry Tech ID: 72148_MMd1-BEER
Tech Name: Registration Private
Tech Organization: Domains By Proxy, LLC
Tech Street: DomainsByProxy.com
Tech Street: 14455 N. Hayden Road
Tech City: Scottsdale
Tech State/Province: Arizona
Tech Postal Code: 85260
Tech Country: US
Tech Phone: +1.4806242599
Tech Fax: +1.4806242598
Tech Email: comicsn.beer@domainsbyproxy.com
Registry Billing ID: 72144_MMd1-BEER
Billing Name: Registration Private
Billing Organization: Domains By Proxy, LLC
Billing Street: DomainsByProxy.com
Billing Street: 14455 N. Hayden Road
Billing City: Scottsdale
Billing State/Province: Arizona
Billing Postal Code: 85260
Billing Country: US
Billing Phone: +1.4806242599
Billing Fax: +1.4806242598
Billing Email: comicsn.beer@domainsbyproxy.com
Name Server: ns58.domaincontrol.com.
Name Server: ns57.domaincontrol.com.
DNSSEC: unsigned
URL of the ICANN Whois Inaccuracy Complaint Form: https://www.icann.org/wicf/
>>> Last update of WHOIS database: 2017-07-21T00:09:31Z <<<
'''


class TestURIHelper(object):

    @classmethod
    def setup(cls):
        logging.getLogger('suds').setLevel(logging.INFO)
        app_settings = TestingConfig()
        cls._urihelper = URIHelper(app_settings)
        # replace collection with mock
        cls._urihelper._db._mongo._collection = mongomock.MongoClient().db.collection
        cls._urihelper._db.add_new_incident(1236, dict(sourceDomainOrIp='lmn.com'))
        cls._urihelper._db.add_new_incident(1237, dict(sourceDomainOrIp='abc.com'))
        cls._urihelper._db.add_new_incident(1237, dict(sourceDomainOrIp='xyz.com', fraud_hold_until=datetime(2016, 5, 11)))
        cls._urihelper._db.add_new_incident(1238, dict(sourceDomainOrIp='cjh.com', fraud_hold_until=datetime(2025, 5, 11)))

    def test_resolves(self):
        true_data = self._urihelper.resolves('http://google.com/')
        assert_true(true_data)
        false_data = self._urihelper.resolves('http://www.nonononononononononono.com/')
        assert_true(false_data is False)

    def test_get_status(self):
        hosted_domain_data = self._urihelper.get_status('comicsn.beer')
        assert_true(hosted_domain_data[0] == URIHelper.HOSTED)
        hosted_ip_data = self._urihelper.get_status('160.153.77.227')
        assert_true(hosted_ip_data[0] == URIHelper.HOSTED)
        nrh_data = self._urihelper.get_status('google.com')
        assert_true(nrh_data[0] == URIHelper.NOT_REG_HOSTED)
        unknown_data = self._urihelper.get_status('abcdefghijklmnopqrstuvwxyz')
        assert_true(unknown_data[0] == URIHelper.UNKNOWN)

    def test_is_ip(self):
        domain_data = self._urihelper._is_ip('http://comicsn.beer/blah/')
        assert_true(domain_data is False)
        ip_data = self._urihelper._is_ip('160.153.77.227')
        assert_true(ip_data)

    def test_is_ip_hosted(self):
        ip_data = self._urihelper._is_ip_hosted('160.153.77.227')
        assert_true(ip_data is True)
        ip_data_2 = self._urihelper._is_ip_hosted('8.8.8.8')
        assert_true(ip_data_2 is False)

    @patch.object(NICClient, 'whois')
    def test_reg_domain_whois(self, data):
        data.return_value = WHOIS_DATA
        domain_data = self._urihelper.domain_whois('comicsn.beer')
        assert_true(domain_data[0] == URIHelper.REG)
        assert_true(domain_data[1] == datetime.strptime('2014-09-25 16:00:13', '%Y-%m-%d %H:%M:%S'))

    def test_nonreg_hosted_domain_whois(self):
        domain_data = self._urihelper.domain_whois('google.com')
        assert_true(domain_data[0] == URIHelper.NOT_REG_HOSTED)

    @patch.object(URIHelper, '_lookup_shopper_info')
    def test_get_shopper_info(self, mocked_method):
        mocked_method.return_value = '<ShopperSearchReturn>' \
                                     '<Shopper ' \
                                     'date_created="1/9/2012 7:41:51 PM" ' \
                                     'first_name="Patrick" ' \
                                     'email="outlawgames@gmail.com" ' \
                                     'shopper_id="49047180"/>' \
                                     '<Shopper ' \
                                     'date_created="7/20/2012 3:00:30 PM" ' \
                                     'first_name="Patrick" ' \
                                     'email="pmcconnell@secureserver.net" ' \
                                     'shopper_id="54459007"/>' \
                                     '</ShopperSearchReturn>'
        expected_time = datetime.strptime('1/9/2012 7:41:51 PM','%m/%d/%Y %I:%M:%S %p')
        sid, created = self._urihelper.get_shopper_info('comicsn.beer')
        assert_equal(sid, "49047180")
        assert_equal(created, expected_time)

    # requires change of test_settings.py KNOX_URL to prod
    # def test_lookup_shopper_info(self):
    # doc = ET.fromstring(self._urihelper._lookup_shopper_info('comicsn.beer'))
    # assert_true(doc is not None)

    def test_no_fraud_holds_for_domain(self):
        assert_false(self._urihelper.fraud_holds_for_domain('abc.com'))

    def test_expired_fraud_hold_for_domain(self):
        assert_false(self._urihelper.fraud_holds_for_domain('xyz.com'))

    def test_existing_fraud_hold_for_domain(self):
        assert_true(self._urihelper.fraud_holds_for_domain('cjh.com') > datetime.utcnow())

