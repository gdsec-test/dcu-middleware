import datetime
import logging
import smtplib
from email.message import EmailMessage

from pymongo import MongoClient
from dcumiddleware.settings import AppConfig

from dcumiddleware.utilities.cmapservicehelper import CmapServiceHelper


class KelvinHelper:
    REQUIRED_FIELDS = ['createdAt', 'kelvinStatus', 'ticketID', 'source',
                       'sourceDomainOrIP', 'type', 'info', 'target', 'proxy',
                       'reporter', 'reporterEmail']

    def __init__(self, config: AppConfig):
        self._logger = logging.getLogger(__name__)
        self._kelvindb = MongoClient(config.KELVIN_DB_URL)[config.KELVIN_DBNAME]
        self._cmapHelper = CmapServiceHelper(config)
        self._genpact_sender = config.GENPACT_SENDER
        self._genpact_receiver = config.GENPACT_RECEIVER
        self._pdna_reporter_id = config.PDNA_REPORTER_ID
        self._shadowfax_reporter_id = config.SHADOWFAX_REPORTER_ID
        self._pdna_reporter_cid = config.PDNA_REPORTER_CID
        self._shadowfax_reporter_cid = config.SHADOWFAX_REPORTER_CID

    def _determine_hosted_status(self, data: dict) -> str:
        ddq = data.get('data', {}).get('domainQuery', {})
        registrar_brand = ddq.get('registrar', {}).get('brand')
        host_brand = ddq.get('host', {}).get('brand')
        if host_brand == 'GODADDY':
            return 'HOSTED'
        elif registrar_brand == 'GODADDY':
            return 'REGISTERED'
        elif host_brand == 'FOREIGN' or registrar_brand == 'FOREIGN':
            return 'FOREIGN'
        else:
            return 'UNKNOWN'

    def _send_email_to_genpact(self, source: str, registrar: str, host: str, ticket_id: str):
        body = f'''URL: {source}\n Registrar:{registrar}\n Host:{host}\n Kelvin ticket No.:
                   {ticket_id} Investigate Further: Investigate Further'''
        s = smtplib.SMTP(host='relay-app.secureserver.net', port=25)
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = 'Potential CSAM content report'
        msg['From'] = self._genpact_sender
        msg['To'] = self._genpact_receiver
        s.send_message(msg)

    def _is_duplicate(self, source: str) -> bool:
        result = self._kelvindb['incidents'].find_one({
            'kelvinStatus': {"$in": ['OPEN', 'AWAITING_INVESTIGATION']},
            'source': source
        })
        if result is not None:
            return True
        return False

    def _update_report_count(self, source: str) -> None:
        selector = {
            'kelvinStatus': {"$in": ['OPEN', 'AWAITING_INVESTIGATION']},
            'source': source
        }
        self._kelvindb['incidents'].update_one(selector, {"$inc": {"report_count": 1}})

    def _write_reporter_email_todb(self, source: str, reporter_email: str):
        email_document = {
            'created': datetime.datetime.now(),
            'email': reporter_email,
            'source': source
        }
        self._kelvindb['acknowledge_email'].insert_one(email_document)

    def process(self, data: dict):
        incidents_collection = self._kelvindb['incidents']
        ticket_id = data.get('ticketID', '')
        # Validate data
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                self._logger.error(f'Missing required field: {field} for ticket id: {ticket_id}')
        # Check duplicate logic
        reporter = data['reporter']
        source = data['source']
        # Shadowfax reporter is allowed to submit duplicate request
        reporter_email = data['reporterEmail']
        if reporter not in [self._shadowfax_reporter_id, self._shadowfax_reporter_cid] and self._is_duplicate(source):
            self._update_report_count(source=source)
            self._write_reporter_email_todb(source=source, reporter_email=reporter_email)
            return
        # Enrich data using cmap service
        cmap_response = {}
        try:
            cmap_response = self._cmapHelper.domain_query_for_kelvindb(source)
        except Exception as e:
            self._logger.exception(e)
            data['failedEnrichment'] = True
        data['hostedStatus'] = self._determine_hosted_status(cmap_response)
        data['data'] = cmap_response.get('data', {})

        if reporter in [self._shadowfax_reporter_id, self._pdna_reporter_id,
                        self._shadowfax_reporter_cid, self._pdna_reporter_cid]:
            data['kelvinStatus'] = 'AWAITING_INVESTIGATION'
        else:
            data['kelvinStatus'] = 'OPEN'
        incidents_collection.insert_one(data)
        self._write_reporter_email_todb(source=source, reporter_email=reporter_email)
        # Send email to genpact
        registrar_name = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('registrarName', '')
        host_name = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('hostingCompanyName', '')
        self._send_email_to_genpact(source=data['source'], registrar=registrar_name, host=host_name, ticket_id=ticket_id)
