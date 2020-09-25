import logging


class TestingConfig:
    LOGLEVEL = logging.INFO
    PROXY = None
    AUTHUSER = None
    FORMAT = '[%(levelname)s:%(asctime)s:%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s'
    DATE_FORMAT = '%Y-%m-%d %I:%M:%S%p'
    DBURL = 'mongodb://localhost/devphishstory'
    DB = 'test'
    COLLECTION = 'test'
    API_UPDATE_URL = None
    API_TOKEN = None
    CMAP_SERVICE = 'http://localhost:5000'
    SSO_URL = ''
    CMAP_CERT = ''
    CMAP_KEY = ''
