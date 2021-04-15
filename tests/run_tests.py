import socket

from dcdatabase.phishstorymongo import PhishstoryMongo
from mock import patch

import run

HOSTED = 'HOSTED'
KEY_FAILED_ENRICHMENT = 'failedEnrichment'
KEY_HOSTED = 'hosted_status'
KEY_PHISHSTORY_STATUS = 'phishstory_status'
KEY_SOURCE_DOMAIN = 'sourceDomainOrIp'
KEY_SUBDOMAIN = 'sourceSubDomain'
KEY_TICKET_ID = 'ticketId'
KEY_TYPE = 'type'
OPEN = 'OPEN'
PHISHING = 'PHISHING'

AUTO_SUSPEND_DOMAIN = {
    'source': 'https://test1.godaddysites.com/',
    KEY_SOURCE_DOMAIN: 'godaddysites.com',
    KEY_SUBDOMAIN: 'test1.godaddysites.com',
    KEY_TICKET_ID: 'DCU001',
    KEY_PHISHSTORY_STATUS: OPEN,
    KEY_HOSTED: HOSTED,
    KEY_TYPE: PHISHING,
    KEY_FAILED_ENRICHMENT: True,
}


class MockCmapServiceHelper:
    def __init__(self, _settings):
        pass

    def domain_query(self, _domain):
        return {'status': 'good'}

    def api_cmap_merge(self, _dict1, _dict2):
        _return = dict()
        _return.update(_dict1)
        _return.update(_dict2)
        return _return


class TestRun:

    # Test successful load and enrichment
    @patch.object(PhishstoryMongo, 'update_incident', return_value=None)
    @patch('run.CmapServiceHelper', return_value=MockCmapServiceHelper({}))
    @patch.object(socket, 'gethostbyname', return_value='1.1.1.1')
    def test_load_and_enrich_data_success(self, mock_socket, mock_cmap, mock_db):
        run._load_and_enrich_data(AUTO_SUSPEND_DOMAIN)
        mock_socket.assert_called()
        mock_cmap.assert_called()
        mock_db.assert_called()
