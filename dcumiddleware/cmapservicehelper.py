import requests
import json


class CmapServiceHelper(object):
	servicenow_url = None
	post_headers = {'Content-Type': 'application/graphql'}

	def __init__(self):
		self.graphene_url = 'http://localhost:5000/graphql'

	def cmap_query(self, query):
		"""
		Returns query result of cmap service given a query
		:param query:
		:return query result:
		"""
		print "Fetching {}".format(query)
		re = requests.post(url=self.graphene_url, headers=self.post_headers, data=query)
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
				      hostNetwork
				    }
				    registrar {
				      name
				    }
				    domainCreateDate {
				      creationDate
				    }
				    profile {
				      Vip
				    }
				    shopperByDomain {
				      shopperId
				      dateCreated
				      domainCount
				    }
				    reseller {
				      parentChild
				    }
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
		merged_data = dict(apidata.items() + cmapdata.items())
		return merged_data


