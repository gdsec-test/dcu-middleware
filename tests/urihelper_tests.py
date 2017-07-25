import logging

from dcumiddleware.urihelper import URIHelper

WHOIS_DATA = '''
Domain Name: COMICSN.BEER
Registry Domain ID: 68841_MMd1-BEER
Registrar WHOIS Server:
Registrar URL:
Updated Date: 2016-09-26T15:03:22Z
Creation Date: 2014-09-25T16:00:13Z
Registry Expiry Date: 2017-09-25T16:00:13Z
Registrar: GoMontenegro
Registrar IANA ID: 1152
Registrar Abuse Contact Email: tho@godaddy.com
Domain Status: CLIENT DELETE PROHIBITED https://icann.org/epp#clientDeleteProhibited
Domain Status: CLIENT RENEW PROHIBITED https://icann.org/epp#clientRenewProhibited
Domain Status: CLIENT TRANSFER PROHIBITED https://icann.org/epp#clientTransferProhibited
Domain Status: CLIENT UPDATE PROHIBITED https://icann.org/epp#clientUpdateProhibited
Registry Registrant ID: 72138_MMd1-BEER
Registrant Name: Registration Private
Registrant Organization: Domains By Proxy, LLC
Registrant Street: DomainsByProxy.com
Registrant Street: 14455 N. Hayden Road
Registrant City: Scottsdale
Registrant State/Province: Arizona
Registrant Postal Code: 85260
Registrant Country: US
Registrant Phone: +1.4806242599
Registrant Fax: +1.4806242598
Registrant Email: comicsn.beer@domainsbyproxy.com
Registry Admin ID: 72141_MMd1-BEER
Admin Name: Registration Private
Admin Organization: Domains By Proxy, LLC
Admin Street: DomainsByProxy.com
Admin Street: 14455 N. Hayden Road
Admin City: Scottsdale
Admin State/Province: Arizona
Admin Postal Code: 85260
Admin Country: US
Admin Phone: +1.4806242599
Admin Fax: +1.4806242598
Admin Email: comicsn.beer@domainsbyproxy.com
Registry Tech ID: 72148_MMd1-BEER
Tech Name: Registration Private
Tech Organization: Domains By Proxy, LLC
Tech Street: DomainsByProxy.com
Tech Street: 14455 N. Hayden Road
Tech City: Scottsdale
Tech State/Province: Arizona
Tech Postal Code: 85260
Tech Country: US
Tech Phone: +1.4806242599
Tech Fax: +1.4806242598
Tech Email: comicsn.beer@domainsbyproxy.com
Registry Billing ID: 72144_MMd1-BEER
Billing Name: Registration Private
Billing Organization: Domains By Proxy, LLC
Billing Street: DomainsByProxy.com
Billing Street: 14455 N. Hayden Road
Billing City: Scottsdale
Billing State/Province: Arizona
Billing Postal Code: 85260
Billing Country: US
Billing Phone: +1.4806242599
Billing Fax: +1.4806242598
Billing Email: comicsn.beer@domainsbyproxy.com
Name Server: ns58.domaincontrol.com.
Name Server: ns57.domaincontrol.com.
DNSSEC: unsigned
URL of the ICANN Whois Inaccuracy Complaint Form: https://www.icann.org/wicf/
>>> Last update of WHOIS database: 2017-07-21T00:09:31Z <<<
'''


class TestURIHelper(object):

    @classmethod
    def setup(cls):
        logging.getLogger('suds').setLevel(logging.INFO)
        cls._urihelper = URIHelper()
