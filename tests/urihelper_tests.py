from nose.tools import assert_true

from settings import TestingConfig
from dcumiddleware.urihelper import URIHelper


class TestURIHelper(object):
	@classmethod
	def setup(cls):
		app_settings = TestingConfig()
		cls._urihelper = URIHelper(app_settings)

	def test_resolves(self):
		true_data = self._urihelper.resolves('http://comicsn.beer/')
		assert_true(true_data is True)
		false_data = self._urihelper.resolves('http://www.nonononononononononono.com/')
		assert_true(false_data is False)

	def test_get_site_data(self):
		site_data = self._urihelper.get_site_data('http://comicsn.beer')
		screenshot = str(site_data[0])
		sourcecode = site_data[1]
		assert_true(screenshot[1] == 'P' and screenshot[2] == 'N' and screenshot[3] == 'G' and sourcecode is not None)
		site_data_2 = self._urihelper.get_site_data('http://')
		screenshot_2 = site_data_2[0]
		sourcecode_2 = site_data_2[1]
		assert_true(screenshot_2 is None and sourcecode_2 is None)

	def test_get_status(self):
		hosted_domain_data = self._urihelper.get_status('http://comicsn.beer/blah/')
		assert_true(hosted_domain_data == URIHelper.HOSTED)
		hosted_ip_data = self._urihelper.get_status('http://160.153.77.227/blah/')
		assert_true(hosted_ip_data == URIHelper.HOSTED)
		nrh_data = self._urihelper.get_status('http://google.com/blah/')
		assert_true(nrh_data == URIHelper.NOT_REG_HOSTED)
		unknown_data = self._urihelper.get_status('abcdefghijklmnopqrstuvwxyz')
		assert_true(unknown_data == URIHelper.UNKNOWN)

	def test_get_ip(self):
		domain_data = self._urihelper._get_ip('http://comicsn.beer/blah/')
		assert_true(domain_data[0] is False)
		ip_data = self._urihelper._get_ip('http://160.153.77.227/blah/')
		assert_true(ip_data[0] is True and ip_data[1] == '160.153.77.227')

	def test_get_domain(self):
		domain_data = self._urihelper._get_domain('http://comicsn.beer/blah/')
		assert_true(domain_data[0] is True and domain_data[1] == 'comicsn.beer')
		domain_data_2 = self._urihelper._get_domain('comicsn.beer')
		assert_true(domain_data_2[0] is True and domain_data[1] == 'comicsn.beer')
		ip_data = self._urihelper._get_domain('http://160.153.77.227/blah/')
		assert_true(ip_data[0] is False)

	def test_is_ip_hosted(self):
		ip_data = self._urihelper._is_ip_hosted('160.153.77.227')
		assert_true(ip_data is True)
		ip_data_2 = self._urihelper._is_ip_hosted('8.8.8.8')
		assert_true(ip_data_2 is False)

	def test_domain_whois(self):
		domain_data = self._urihelper._domain_whois('comicsn.beer')
		assert_true(domain_data == URIHelper.REG)
		domain_data_2 = self._urihelper._domain_whois('google.com')
		assert_true(domain_data_2 == URIHelper.NOT_REG_HOSTED)
