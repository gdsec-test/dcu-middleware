import logging
import re
import psutil
import socket
import xml.etree.ElementTree as ET
import signal
from datetime import datetime, timedelta

import requests
from dcdatabase.phishstorymongo import PhishstoryMongo
from ipwhois import IPWhois
from selenium import webdriver
from suds.client import Client
from whois import NICClient
from requests import sessions


class URIHelper:
    # Status values
    HOSTED = 1
    REG = 2
    NOT_REG_HOSTED = 3
    UNKNOWN = -1
    GD_PHISH = [
        re.compile('(rebrand-bg-image\.jpg|bg-pass\.png)'),
        re.compile('Sign in'),
        re.compile('\.wsimg\.com'),
        re.compile('\$\( *\'form\[id=login-form\]\' *\)\.attr\( *\'action\''),
        re.compile('GoDaddy Operating Company, LLC')
    ]

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._db = PhishstoryMongo(settings)
        self._url = settings.KNOX_URL

    def gd_phish(self, source_code):
        """
        Detects if the given sourcecode is attempting to phish GoDaddy
        :return: True if at least 2 of the GD_PHISH regexes match the given sourcecode
        """
        match = []
        try:
            match = [y.search(source_code) for y in self.GD_PHISH]
            match = filter(None, match)
        except Exception as e:
            self._logger.error("Unable to determine if sourcecdode is a GD_PHISH:%s", e)
        return len(match) > 1

    def resolves(self, url):
        """
        Returns a boolean indicating whether the site resolves or not
        :param url:
        :return:
        NOTE: If we are using auth, requests library will not resend auth on a redirect (will result in a 401),
        so we need to manually check for one and re-issue the get with the redirected url and the auth credentials
        """
        try:
            with sessions.Session() as session:
                bad_site = session.request(method='GET', url=url, timeout=60)
                status = str(bad_site.status_code)
                if status[0] in ["1", "2", "3"]:
                    return True
                elif status == "406":
                    return True
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
        data = (None, None)
        try:
            browser = webdriver.PhantomJS()
            browser.set_page_load_timeout(10)
            browser.get(url)
            screenshot = browser.get_screenshot_as_png()
            sourcecode = browser.page_source.encode('ascii', 'ignore')
            data = (screenshot, sourcecode)
            return data
        except Exception as e:
            self._logger.error("Error while taking snapshot and/or source code for %s: %s", url, str(e))
            return data
        finally:
            try:
                browser.service.process.send_signal(signal.SIGTERM)
                browser.quit()
            except:
                pass

    def get_status(self, sourceDomainOrIp):
        """
        Returns a tuple
        Possible return value for first in tuple could be HOSTED, REG, NOT_REG_HOSTED
        Possible return value for second in tuple is the creation date of a registered only domain or None if registered
        elsewhere
        :param sourceDomainOrIp:
        :return:
        """

        try:
            # is it an ip address?
            if self._is_ip(sourceDomainOrIp):
                ip_hosted = self._is_ip_hosted(sourceDomainOrIp)
                return (URIHelper.HOSTED, None) if ip_hosted else (URIHelper.NOT_REG_HOSTED, None)
            else:
                try:
                    ip = socket.gethostbyname(sourceDomainOrIp)
                except socket.gaierror:
                    # Add www if not present, else remove and try again
                    domain = 'www.' + sourceDomainOrIp if sourceDomainOrIp[:4] != 'www.' else sourceDomainOrIp[4:]
                    ip = socket.gethostbyname(domain)
                if ip == '0.0.0.0':
                    raise Exception("Invalid Host")
                ip_hosted = self._is_ip_hosted(ip)
                return (URIHelper.HOSTED, None) if ip_hosted else self.domain_whois(sourceDomainOrIp)

        except Exception as e:
            self._logger.error("Error in determining state of {}:{}".format(sourceDomainOrIp, e.message))
            return URIHelper.UNKNOWN, None

    def _is_ip(self, sourceDomainOrIp):
        """
        Returns whether the given sourceDomainOrIp is an ip address
        :param sourceDomainOrIp:
        :return:
        """
        pattern = re.compile(r"((([01]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])[ (\[]?(\.|dot)[ )\]]?){3}[0-9]{1,3})")
        return pattern.match(sourceDomainOrIp) is not None

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
            self._logger.warning("Error in reverse DNS lookup %s : %s, attempting whois lookup..", ip, e.message)
            regex = re.compile('[^a-zA-Z]')
            name = regex.sub('', IPWhois(ip).lookup_rdap().get('network', []).get('name', ''))
            return 'GODADDY' in name.upper()

    def domain_whois(self, domain_name):
        """
        Returns a tuple
        Possible return value for first in tuple could be REG or NOT_REG_HOSTED based on being registered with GoDaddy
        or elsewhere
        Possible return value for second in tuple is the creation date of a registered only domain or None if registered
        elsewhere
        :param domain_name:
        :return:
        """
        whois_server = 'whois.godaddy.com'
        nicclient = NICClient()
        domain_name = domain_name[4:] if domain_name[:4] == 'www.' else domain_name
        try:
            domain = nicclient.whois(domain_name, whois_server, True)
            if "No match" not in domain:
                try:
                    # get creation date from whois and format it
                    creation_date = datetime.strptime(re.search(r'Creation Date:\s?(\S+)', domain).group(1),
                                                      '%Y-%m-%dT%H:%M:%SZ')
                    return URIHelper.REG, creation_date
                except Exception as e:
                    self._logger.error("Error in determing create date of %s : %s", domain_name, e.message)
                    return URIHelper.REG, None
            else:
                return URIHelper.NOT_REG_HOSTED, None
        except Exception as e:
            self._logger.error("Error in determing whois of %s : %s", domain_name, e.message)
            return URIHelper.UNKNOWN, None

    def get_shopper_info(self, domain):
        """
        Returns a tuple containing the shopper id, and the date created
        :param domain:
        :return:
        """
        try:
            doc = ET.fromstring(self._lookup_shopper_info(domain))
            elem = doc.find(".//*[@shopper_id]")
            return elem.get('shopper_id'), datetime.strptime(elem.get('date_created'), '%m/%d/%Y %I:%M:%S %p')
        except Exception as e:
            self._logger.error("Unable to lookup shopper info for {}:{}".format(domain, e))
            return None, None

    def _lookup_shopper_info(self, domain):
        """
        Returns the xml representing the shopper id(s)
        :param domain:
        :return:
        """
        shopper_search = ET.Element("ShopperSearch", IPAddress='', RequestedBy='DCU-ENG')
        searchFields = ET.SubElement(shopper_search, 'SearchFields')
        ET.SubElement(searchFields, 'Field', Name='domain').text = domain

        returnFields = ET.SubElement(shopper_search, "ReturnFields")
        ET.SubElement(returnFields, 'Field', Name='shopper_id')
        ET.SubElement(returnFields, 'Field', Name='date_created')
        xmlstr = ET.tostring(shopper_search, encoding='utf8', method='xml')
        # The following Fort Knox client will timeout on the dev side, unless a firewall rule is created
        #  allowing access from dev Rancher, which means no shopper id, account create date, etc when
        #  running from dev
        client = Client(self._url, timeout=5)
        return client.service.SearchShoppers(xmlstr)

    def fraud_holds_for_domain(self, domain):
        """
        Returns any valid(Non-expired) holds for the given tickets domain
        :param domain
        :return:
        """
        try:
            query = dict(phishstory_status='OPEN', sourceDomainOrIp=domain, fraud_hold_until={'$exists': True})
            domain_ticket = self._db.find_incidents(query, [('fraud_hold_until', 1)], 1)
            if domain_ticket and domain_ticket[0]['fraud_hold_until'] > datetime.utcnow():
                return domain_ticket[0]['fraud_hold_until']
        except Exception as e:
            self._logger.error("Unable to determine any fraud holds for {}:{}".format(domain, e.message))

    def _cleanup_old_phantomjs_processes(self):
        """
        Phantomjs has a nasty bug that leaves processes laying around
        after they have been quit from. This causes a memory leak. This
        function will kill off any processes that have been lying around
        for 10 mins or more
        """
        try:
            for proc in psutil.process_iter():
                if proc.name() == 'phantomjs':
                    p = psutil.Process(proc.pid)
                    date = datetime.fromtimestamp(p.create_time())
                    if date < datetime.utcnow() - timedelta(minutes=10):
                        p.terminate()
        except Exception as e:
            self._logger.error("Unbale to remove old phantomjs processes {}".format(e))
