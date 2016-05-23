import settings
import os
from nose.tools import assert_true


class TestSettings:

	@classmethod
	def setup_class(cls):
		os.environ['DBPASS'] = 'vkdE4NSw5wgFIcQDxQ=='  # decrypted password: test_password
		path = os.getcwd()+'/tests/'
		os.environ['KEYFILE'] = path+'test_key.txt'
		os.environ['AUTHPASS'] = 'gDUP2rTdDPk='  # decrypted password: JmpxL72s

	def test_app_config(self):
		configs = settings.AppConfig()
		assert_true(configs.AUTHPASS == 'JmpxL72s')

	def test_production_app_config(self):
		configs = settings.ProductionAppConfig()
		assert_true(configs.PASS == 'vkdE4NSw5wgFIcQDxQ==')
		assert_true(configs.DBURL == 'mongodb://sau_p_phish:test_password@10.22.9.209/phishstory')

	def test_ote_app_config(self):
		configs = settings.OTEAppConfig()
		assert_true(configs.PASS == 'vkdE4NSw5wgFIcQDxQ==')
		assert_true(configs.DBURL == 'mongodb://sau_p_phish:test_password@10.22.9.209/phishstory')
