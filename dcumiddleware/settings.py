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

    CMAP_CLIENT_CERT = os.getenv('CMAP_CLIENT_CERT')
    CMAP_CLIENT_KEY = os.getenv('CMAP_CLIENT_KEY')

    SHOPPER_API_URL = os.getenv('SHOPPER_API_URL')
    SHOPPER_API_CERT_PATH = os.getenv('SHOPPER_API_CERT_PATH')
    SHOPPER_API_KEY_PATH = os.getenv('SHOPPER_API_KEY_PATH')

    REGISTERED_ONLY_PRODUCTS = {'Shortener', 'Parked', 'EOL', 'GEM'}
    SSO_URL = 'https://sso.dev-gdcorp.tools'
    SSO_USER = os.getenv('SSO_USER', 'user')
    SSO_PASSWORD = os.getenv('SSO_PASSWORD', 'password')
    # config for kelvin sync
    SHADOWFAX_REPORTER_ID = ''
    SHADOWFAX_REPORTER_CID = ''
    PDNA_REPORTER_ID = ''
    PDNA_REPORTER_CID = ''
    GENPACT_SENDER = ''
    GENPACT_RECEIVER = ''
    KELVIN_DB_URL = os.getenv('KELVIN_DB_URL')
    KELVIN_DBNAME = ''

    BROKER_URL = os.getenv('MULTIPLE_BROKERS')

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

    PDNA_REPORTER_ID = '222151473'
    PDNA_REPORTER_CID = 'c4e19017-2259-453a-96d0-95466f144ded'
    SHADOWFAX_REPORTER_ID = '350853785'
    SHADOWFAX_REPORTER_CID = 'f8a4ab73-8892-486f-98b9-4f6ba6d1048a'
    GENPACT_SENDER = 'cst-gp@godaddy.com'
    GENPACT_RECEIVER = 'prod_trustandsafety@z-c2fbrs90d9ediwdjd88zl485ikgyej58hyuf56omumxiclcih.f2-1g8e2eak.na173.apex.salesforce.com'
    KELVIN_DBNAME = 'dcu_kelvin'

    SSO_URL = 'https://sso.gdcorp.tools'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    DB = 'otephishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_o_phish'

    APIQUEUE = 'otedcumiddleware'
    GDBRANDSERVICESQUEUE = 'otegdbrandservice'
    EMEABRANDSERVICESQUEUE = 'oteemeabrandservice'

    PDNA_REPORTER_ID = '1500319040'
    PDNA_REPORTER_CID = 'eb80d7fe-1c19-419e-9039-da36b53bdee8'
    SHADOWFAX_REPORTER_ID = '1500566424'
    SHADOWFAX_REPORTER_CID = 'c490ad3c-a501-45e2-80a5-cfbf2a890f65'
    GENPACT_SENDER = 'test-cst-gp@godaddy.com'
    GENPACT_RECEIVER = 'test-cst-gp@2w2zapmulv96i8lbcolvhkwvoy5fkpvaexo0bnci8klryyaokx.29-ekkfea4.cs19.apex.sandbox.salesforce.com'
    KELVIN_DBNAME = 'ote_dcu_kelvin'

    SSO_URL = 'https://sso.ote-gdcorp.tools'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class TestAppConfig(AppConfig):
    DB = 'testphishstory'
    DB_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_USER = 'testuser'

    APIQUEUE = 'testdcumiddleware'
    GDBRANDSERVICESQUEUE = 'testgdbrandservice'
    EMEABRANDSERVICESQUEUE = 'testemeabrandservice'

    PDNA_REPORTER_ID = '4051952'
    PDNA_REPORTER_CID = 'f2f9341e-48e8-4db1-8152-05da9609b99b'
    SHADOWFAX_REPORTER_ID = '4051952'
    SHADOWFAX_REPORTER_CID = 'f2f9341e-48e8-4db1-8152-05da9609b99b'
    GENPACT_SENDER = 'test-cst-gp@godaddy.com'
    GENPACT_RECEIVER = 'test-cst-gp@2w2zapmulv96i8lbcolvhkwvoy5fkpvaexo0bnci8klryyaokx.29-ekkfea4.cs19.apex.sandbox.salesforce.com'
    KELVIN_DBNAME = 'testkelvin'

    SSO_URL = 'https://sso.test-gdcorp.tools'

    def __init__(self):
        super(TestAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_USER = 'devuser'

    APIQUEUE = 'devdcumiddleware'
    GDBRANDSERVICESQUEUE = 'devgdbrandservice'
    EMEABRANDSERVICESQUEUE = 'devemeabrandservice'

    PDNA_REPORTER_ID = '1767806'
    PDNA_REPORTER_CID = '4eddbbb1-2abc-4c82-a129-3209723ffc12'
    SHADOWFAX_REPORTER_ID = '4051952'
    SHADOWFAX_REPORTER_CID = 'f2f9341e-48e8-4db1-8152-05da9609b99b'
    GENPACT_SENDER = 'test-cst-gp@godaddy.com'
    GENPACT_RECEIVER = 'test-cst-gp@2w2zapmulv96i8lbcolvhkwvoy5fkpvaexo0bnci8klryyaokx.29-ekkfea4.cs19.apex.sandbox.salesforce.com'
    KELVIN_DBNAME = 'devkelvin'

    SSO_URL = 'https://sso.dev-gdcorp.tools'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class UnitTestAppConfig(AppConfig):
    DBURL = 'mongodb://devuser:phishstory@mongodb.cset.int.dev-gdcorp.tools/devphishstory'
    DB = 'devphishstory'

    APIQUEUE = 'testdcumiddleware'
    GDBRANDSERVICESQUEUE = ''
    EMEABRANDSERVICESQUEUE = ''

    SSO_URL = 'https://sso.gdcorp.tools'


config_by_name = {'dev': DevelopmentAppConfig, 'prod': ProductionAppConfig, 'ote': OTEAppConfig,
                  'unit-test': UnitTestAppConfig, 'test': TestAppConfig}
