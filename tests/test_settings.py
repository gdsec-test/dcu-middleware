from settings import DevelopmentAppConfig


class TestingConfig(DevelopmentAppConfig):
    DBURL = 'mongodb://localhost/devphishstory'
