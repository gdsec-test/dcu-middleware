import requests
import json


class GrapheneAccess(object):
	servicenow_url = None
	post_headers = {'Content-Type': 'application/graphql'}

	def __init__(self):
		self.graphene_url = 'http://localhost:5000/graphql'

	def get_hash(self, query):
		print "Fetching {}".format(query)
		re = requests.post(url=self.graphene_url, headers=self.post_headers, data=query)
		return json.loads(re.text)

	def domain_query(self, domain):
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
		query_result = self.get_hash(query)
		return query_result

	def api_cmap_merge(self, apidata, cmapdata):
		merged_data = dict(apidata.items() + cmapdata.items())
		return merged_data

if __name__ == '__main__':
	apidata = {'info': u'My spam Farm is better than yours...',
				 'sourceDomainOrIp': u'spam.com',
				 'ticketId': u'DCU000001053',
				 'target': u'The spam Brothers',
				 'reporter': u'bxberry',
				 'source': u'http://spam.com/thegoodstuff/jonas.php?g=a&itin=1324',
				 'proxy': u'Must be viewed from an German IP',
				 'type': u'PHISHING'}

	graphene = GrapheneAccess()
	cmapdata = graphene.domain_query("comicsn.beer")
	merged_data = graphene.api_cmap_merge(apidata, cmapdata)
	print merged_data
