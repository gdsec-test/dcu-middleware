from dcdatabase.phishstorymongo import PhishstoryMongo


class TicketHelper:

    def __init__(self, settings):
        self._db = PhishstoryMongo(settings)

    def domain_for_ticket(self, ticket):
        """
        Returns the domain for the given ticket
        :param ticket:
        :return:
        """
        doc = self._db.get_incident(ticket)
        if doc:
            return doc.get('sourceDomainOrIp', None)
