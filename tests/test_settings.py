from settings import DevelopmentAppConfig


class TestingConfig(DevelopmentAppConfig):
    DBHOST='localhost'
    DBPORT=27017
    DB='phishstory'
    COLLECTION='incidents'
