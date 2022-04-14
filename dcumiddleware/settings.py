import os
import urllib.parse


class AppConfig(object):
    DBURL = 'localhost'
    DB = 'test'
    DB_USER = 'user'
    DB_HOST = 'localhost'
    BLACKLIST_COLLECTION = 'blacklist'
    COLLECTION = 'incidents'

    # The sub-domains for these domains have the same ip as the domain ip, but we get better
    #  enrichment querying on the sub-domain
    ENRICH_ON_SUBDOMAIN = {'godaddysites.com'}

    CMAP_SERVICE = os.getenv('SERVICE_URL', 'service')

    ABUSE_API_URL = os.getenv('ABUSE_API_URL', 'https://abuse.api.int.dev-godaddy.com/v1/abuse/tickets')

    # Time in seconds to time-out a task
    TASK_TIMEOUT = 1
    # The number of times to retry a task after every TASK_TIMEOUT seconds
    TASK_MAX_RETRIES = 2

    CMAP_CERT = os.getenv('CMAP_CERT')
    CMAP_KEY = os.getenv('CMAP_KEY')

    SHOPPER_API_URL = os.getenv('SHOPPER_API_URL')
    SHOPPER_API_CERT_PATH = os.getenv('SHOPPER_API_CERT_PATH')
    SHOPPER_API_KEY_PATH = os.getenv('SHOPPER_API_KEY_PATH')

    REGISTERED_ONLY_PRODUCTS = {'Shortener', 'Parked', 'EOL', 'GEM'}
    SSO_URL = 'https://sso.dev-godaddy.com'
    SSO_USER = os.getenv('SSO_USER', 'user')
    SSO_PASSWORD = os.getenv('SSO_PASSWORD', 'password')

    # TODO CMAPT-5032: remove this
    QUEUE_TYPE = os.getenv('QUEUE_TYPE', 'classic')
    # TODO CMAPT-5032: remove everything after & including "if QUORUMQUEUE"
    BROKER_URL = os.getenv('MULTIPLE_BROKERS') if QUEUE_TYPE == 'quorum' else os.getenv('SINGLE_BROKER')

    def __init__(self):
        self.DB_PASS = urllib.parse.quote(os.getenv('DB_PASS', 'password'))
        self.DBURL = 'mongodb://{}:{}@{}/{}'.format(self.DB_USER, self.DB_PASS, self.DB_HOST, self.DB)


class ProductionAppConfig(AppConfig):
    DB = 'phishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_p_phishv2'

    APIQUEUE = 'dcumiddleware'
    GDBRANDSERVICESQUEUE = 'gdbrandservice'
    EMEABRANDSERVICESQUEUE = 'emeabrandservice'

    TASK_TIMEOUT = 60 * 60
    TASK_MAX_RETRIES = 4

    SSO_URL = 'https://sso.godaddy.com'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    DB = 'otephishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_o_phish'

    APIQUEUE = 'otedcumiddleware'
    GDBRANDSERVICESQUEUE = 'otegdbrandservice'
    EMEABRANDSERVICESQUEUE = 'oteemeabrandservice'

    SSO_URL = 'https://sso.ote-godaddy.com'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class TestAppConfig(AppConfig):
    DB = 'testphishstory'
    DB_HOST = '10.36.156.188'
    DB_USER = 'testuser'

    APIQUEUE = 'testdcumiddleware'
    GDBRANDSERVICESQUEUE = 'testgdbrandservice'
    EMEABRANDSERVICESQUEUE = 'testemeabrandservice'

    SSO_URL = 'https://sso.test-godaddy.com'

    def __init__(self):
        super(TestAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = '10.36.156.188'
    DB_USER = 'devuser'

    APIQUEUE = 'devdcumiddleware'
    GDBRANDSERVICESQUEUE = 'devgdbrandservice'
    EMEABRANDSERVICESQUEUE = 'devemeabrandservice'

    SSO_URL = 'https://sso.dev-godaddy.com'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class UnitTestAppConfig(AppConfig):
    DBURL = 'mongodb://devuser:phishstory@10.36.156.188/devphishstory'
    DB = 'devphishstory'

    APIQUEUE = 'testdcumiddleware'
    GDBRANDSERVICESQUEUE = ''
    EMEABRANDSERVICESQUEUE = ''

    SSO_URL = 'https://sso.godaddy.com'


config_by_name = {'dev': DevelopmentAppConfig, 'prod': ProductionAppConfig, 'ote': OTEAppConfig,
                  'unit-test': UnitTestAppConfig, 'test': TestAppConfig}
