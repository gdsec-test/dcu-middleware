import logging

from pyvirtualdisplay import Display
from selenium import webdriver
from tld import get_tld
from whois import NICClient

class URIHelper:

    # Status values
    HOSTED = 1
    REG = 2
    NOT_REG_HOSTED = 3

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)

    def resolves(self, url):
        """
        Returns a boolean indicating whether the site resolves or not
        :param url:
        :return:
        """

    def get_site_data(self, url):
        """
        Returns a tuple consisting of screenshot, and sourcecode for the url in question
        :return:
        """

    def get_status(self, uri):
        """
        Returns a integral value indicating the state of the URI passed in. This could be a url, or an ip.
        Possible return values could be HOSTED, REG, NOT_REG_HOSTED
        :param uri:
        :return:
        """