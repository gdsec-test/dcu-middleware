import logging
import re
from datetime import datetime
from pprint import pformat

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.dcuapi_functions import DCUAPIFunctions
from dcumiddleware.interfaces.strategy import Strategy
from dcumiddleware.urihelper import URIHelper
# from dcumiddleware.viphelper import CrmClientApi, RegDbAPI, VipClients, RedisCache
from dcumiddleware.viphelper import VipClients, RedisCache

from cmapservicehelper import CmapServiceHelper


class PhishingStrategy(Strategy):

	def __init__(self, settings):
		self._logger = logging.getLogger(__name__)
		self._urihelper = URIHelper(settings)
		self._db = PhishstoryMongo(settings)
		self._api = DCUAPIFunctions(settings)
		self._cmapservice = CmapServiceHelper()
		_redis = RedisCache(settings)
		# self._premium = CrmClientApi(_redis)
		# self._regdb = RegDbAPI(_redis)
		self._vip = VipClients(settings, _redis)

	def close_process(self, data, close_reason):
		data['close_reason'] = close_reason
		self._db.close_incident(data.get('ticketId'), data)
		# Close upstream ticket as well
		if self._api.close_ticket(data.get('ticketId')):
			self._logger.info("Ticket {} closed successfully".format(data.get('ticketId')))
		else:
			self._logger.warning("Unable to close upstream ticket {}".format(data.get('ticketId')))
		return data

	def process(self, data, **kwargs):
		# determine if domain is hosted at godaddy

		self._logger.info("Received request {}".format(pformat(data)))

		cmapdata = self._cmapservice.domain_query(data['sourceDomainOrIp'])

		status = None

		try:
			merged_data = self._cmapservice.api_cmap_merge(data, cmapdata)

			# regex to determine if godaddy is the host and registrar
			regex = re.compile('[^a-zA-Z]')
			host = merged_data['data']['domainQuery']['host']['hostNetwork']
			hostname = regex.sub('', host)
			reg = merged_data['data']['domainQuery']['registrar']['name']
			registrar = regex.sub('', reg)

			if 'GODADDY' in hostname.upper():
				status = "HOSTED"
			elif 'GODADDY' in registrar.upper():
				status = "REGISTERED"
			elif 'GODADDY' not in hostname.upper() and 'GODADDY' not in registrar.upper():
				status = "FOREIGN"
		except Exception as e:
			self._logger.warn("Unknown registrar/host status for incident: {}. {}".format(pformat(data), e.message))
			status = "UNKNOWN"
			merged_data = data

		merged_data['hosted_status'] = status
		if status in ["FOREIGN", "UNKNOWN"]:
			return self.close_process(merged_data, "unworkable")

		# add domain create date if domain is registered only
		if status is "REGISTERED":
			merged_data['d_create_date'] = merged_data['data']['domainQuery']['domainCreateDate']['creationDate']

		# add shopper info if we can find it
		sid = merged_data['data']['domainQuery']['shopperByDomain']['shopperId']
		s_create_date = merged_data['data']['domainQuery']['shopperByDomain']['dateCreated']

		if sid and s_create_date:
			merged_data['sid'] = sid
			merged_data['s_create_date'] = s_create_date

			# if shopper is premium, add it to their mongo record
			premier = merged_data['data']['domainQuery']['profile']['Vip']
			if premier:
				merged_data['premier'] = premier

			# get the number of domains in the shopper account
			domain_count = merged_data['data']['domainQuery']['shopperByDomain']['domainCount']
			if domain_count is not None:
				merged_data['domain_count'] = domain_count

			# get parent/child reseller api account status
			# TODO: This code should be moved outside of the (if sid and s_create_date) block, as it is independent
			parentchild = merged_data['data']['domainQuery']['reseller']['parentChild']
			if 'No Parent/Child Info Found' not in parentchild:
				parentchild = str(parentchild).split(',')
				merged_data['parent_api_account'] = parentchild[0].split(':')[1]
				merged_data['child_api_account'] = parentchild[1].split(':')[1]

			# get blacklist status - DO NOT SUSPEND special shopper accounts
			if self._vip.query_blacklist(sid):
				merged_data['blacklist'] = True

			# get blacklist status - DO NOT SUSPEND special domain
			# TODO: This code should be moved outside of the (if sid and s_create_date) block, as it is independent
			if self._vip.query_blacklist(data.get('sourceDomainOrIp')):
				merged_data['blacklist'] = True

		else:
			# TODO: Implement a better way to determine if the vip status is Unconfirmed
			merged_data['vip_unconfirmed'] = True

		# Add hosted_status to incident
		res = self._urihelper.resolves(merged_data.get('source'))
		if res or merged_data.get('proxy'):
			iid = self._db.add_new_incident(merged_data.get('ticketId'), merged_data)
			if iid:
				self._logger.info("Incident {} inserted into database".format(iid))
				if res:
					# Attach crits data if it resolves
					source = merged_data.get('source')
					screenshot_id, sourcecode_id = self._db.add_crits_data(self._urihelper.get_site_data(source),
																		   source)
					merged_data = self._db.update_incident(iid, dict(screenshot_id=screenshot_id,
															  sourcecode_id=sourcecode_id,
															  last_screen_grab=datetime.utcnow()))
			else:
				self._logger.error("Unable to insert {} into database".format(iid))
		else:
			merged_data = self.close_process(data, "unresolvable")

		return merged_data
