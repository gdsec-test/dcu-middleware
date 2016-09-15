import logging


class TestingConfig():
    LOGLEVEL = logging.INFO
    PROXY = None
    AUTHUSER = None
    AUTHPASS = None
    FORMAT = "[%(levelname)s:%(asctime)s:%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    DATE_FORMAT = '%Y-%m-%d %I:%M:%S%p'
    DBURL = 'mongodb://localhost/devphishstory'
    DB = 'test'
    COLLECTION = 'test'
    API_UPDATE_URL = None
    API_TOKEN = None
    KNOX_URL = 'https://shopper.test.glbt1.gdg/WSCgdShopper/WSCgdShopper.dll?Handler=GenWSCgdShopperWSDL'
    # KNOX_URL = 'http://shopper.prod.mesa1.gdg/WSCgdShopper/WSCgdShopper.dll?Handler=GenWSCgdShopperWSDL'  # Prod
    HOLD_TIME = 86400