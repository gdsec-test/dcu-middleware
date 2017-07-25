import logging
import signal

from dcdatabase.phishstorymongo import PhishstoryMongo
from selenium import webdriver


class URIHelper:

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._db = PhishstoryMongo(settings)
        self._url = settings.KNOX_URL

    def get_site_data(self, url):
        """
        Returns a tuple consisting of screenshot, and sourcecode for the url in question
        :param url:
        :return:
        """
        try:
            browser = webdriver.PhantomJS()
            browser.set_page_load_timeout(10)
            browser.get(url)
            screenshot = browser.get_screenshot_as_png()
            sourcecode = browser.page_source.encode('ascii', 'ignore')
            return screenshot, sourcecode
        except Exception as e:
            self._logger.error("Error while taking snapshot and/or source code for %s: %s", url, str(e))
        finally:
            browser.service.process.send_signal(signal.SIGTERM)
            browser.quit()
