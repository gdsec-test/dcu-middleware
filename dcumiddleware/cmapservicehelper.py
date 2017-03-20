import requests
import json


class CmapServiceHelper(object):
	# servicenow_url = None

	def __init__(self, settings):
		self._graphene_url = settings.CMAP_SERVICE + '/graphql'
		self._post_headers = {'Content-Type': 'application/graphql'}

	def cmap_query(self, query):
		"""
		Returns query result of cmap service given a query
		:param query:
		:return query result:
		"""
		# TODO : remove print, add loging, add try except
		print "Fetching {}".format(query)
		re = requests.post(url=self._graphene_url, headers=self._post_headers, data=query)
		return json.loads(re.text)

	def domain_query(self, domain):
		"""
		Returns query result of cmap service given a domain
	    :param domain:
	    :return query result: query result host, registrar, domain create date, vip profile, shopperID, shopper create date,
	    shopper domain count, API parent/child account numbers
		"""
		query = ('''
				{
				  domainQuery(domain: "''' + domain + '''") {
				    host {
				      name
				    }
				    registrar {
				      name
				      createDate
				    }
				    apiReseller {
				      parent
				      child
				    }
				    shopperInfo {
				      shopperId
				      dateCreated
				      domainCount
				      vip {
				        blacklist
				        PortfolioType
				      }
				    }
				    blacklist
				  }
				}
				''')
		query_result = self.cmap_query(query)
		return query_result

	def api_cmap_merge(self, apidata, cmapdata):
		"""
		Returns query result of cmap service given a domain
		:param apidata, cmapdata:
		:return merged_data: dictionary that is the result of merging the api data and cmap data dictionaries
		"""
		# TODO : add loging and try/except
		merged_data = dict(apidata.items() + cmapdata.items())
		return merged_data
