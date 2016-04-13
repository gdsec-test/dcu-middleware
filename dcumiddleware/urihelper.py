import logging
import re
import socket

import requests
from pyvirtualdisplay import Display
from selenium import webdriver
from tld import get_tld
from whois import NICClient


class URIHelper:

    # Status values
    HOSTED = 1
    REG = 2
    NOT_REG_HOSTED = 3
    UNKNOWN = -1

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._proxy = settings.PROXY

    def resolves(self, url):
        """
        Returns a boolean indicating whether the site resolves or not
        :param url:
        :return:
        """
        try:
            bad_site = requests.get(url, proxies=self._proxy, timeout=60)
            status = str(bad_site.status_code)
            if status[0] in ["1", "2", "3"]:
                return True
            # elif status == "406":
                # return False
            else:
                return False
        except Exception as e:
            self._logger.error("Error in determining if url resolves %s : %s", url, e.message)
            return False

    def get_site_data(self, url):
        """
        Returns a tuple consisting of screenshot, and sourcecode for the url in question
        :param url:
        :return:
        """
        display = Display(visible=0, size=(800, 600))
        display.start()
        browser = webdriver.Firefox()
        data = None
        try:
            browser.set_page_load_timeout(30)
            browser.get(url)
            screenshot = browser.get_screenshot_as_png()
            sourcecode = browser.page_source.encode('ascii', 'ignore')
            data = (screenshot, sourcecode)
        except Exception as e:
            self._logger.error("Error while taking snapshot and/or source code for %s: %s", url, e.message)
        finally:
            browser.quit()
            display.stop()
            return data

    def get_status(self, uri):
        """
        Returns a integral value indicating the state of the URI passed in. This could be a url, or an ip.
        Possible return values could be HOSTED, REG, NOT_REG_HOSTED
        :param uri:
        :return:
        """

        try:
            ip_results = self._get_ip(uri)
            domain_results = self._get_domain(uri)

            if ip_results[0]:
                ip_hosted = self._is_ip_hosted(ip_results[1])
                return URIHelper.HOSTED if ip_hosted else URIHelper.NOT_REG_HOSTED

            elif domain_results[0]:
                ip = socket.gethostbyname(domain_results[1])
                ip_hosted = self._is_ip_hosted(ip)
                return URIHelper.HOSTED if ip_hosted else self._domain_whois(domain_results[1])

            else:
                return URIHelper.UNKNOWN

        except Exception as e:
            self._logger.error("Error in determining state of URI %s: %s", uri, e.message)
            return URIHelper.UNKNOWN

    def _get_ip(self, uri):
        """
        Returns a tuple of either True with an IP or False and null based on whether an IP was found in uri.
        :param uri:
        :return:
        """
        try:
            pattern = re.compile(r"((([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])[ (\[]?(\.|dot)[ )\]]?){3}[0-9]{1,3})")
            ip = [match[0] for match in re.findall(pattern, uri)][0]
            ip_results = (True, ip)
            return ip_results
        except Exception as e:
            self._logger.error("Error in finding an IP in %s: %s", uri, e.message)
            ip_results = (False, )
            return ip_results

    def _get_domain(self, uri):
        """
        Returns a tuple of either True with a domain or False and null based on whether an domain was found in uri.
        :param uri:
        :return:
        """
        try:
            domain_name = get_tld(uri, fail_silently=True) or uri
            domain_results = (True, domain_name)
            if domain_name != uri:
                return domain_results
            else:
                uri = 'http://'+uri
                domain_name = get_tld(uri)
                domain_results = (True, domain_name)
                return domain_results
        except Exception as e:
            self._logger.error("Error in finding a domain in %s : %s", uri, e.message)
            domain_results = (False, )
            return domain_results

    def _is_ip_hosted(self, ip):
        """
        Returns True or False based on whether "secureserver" was found in the server name in a nslookup of the IP.
        :param ip:
        :return:
        """
        try:
            ip_lookup = socket.gethostbyaddr(ip)
            server_name = ip_lookup[0]
            # split up server name and find domain before TLD
            server_name_array = server_name.split(".")
            server_domain = server_name_array[len(server_name_array) - 2]
            return server_domain == "secureserver"
        except Exception as e:
            self._logger.error("Error in determining server name of %s : %s", ip, e.message)
            return False

    def _domain_whois(self, domain_name):
        """
        Returns REG or NOT_REG_HOSTED based on a domain registered with GoDaddy or elsewhere
        :param domain_name:
        :return:
        """
        whois_server = 'whois.godaddy.com'
        nicclient = NICClient()
        try:
            domain = nicclient.whois(domain_name, whois_server, True)
            if "No match" not in domain:
                return URIHelper.REG
            else:
                return URIHelper.NOT_REG_HOSTED
        except Exception as e:
            self._logger.error("Error in determing whois of %s : %s", domain_name, e.message)
            return URIHelper.UNKNOWN
