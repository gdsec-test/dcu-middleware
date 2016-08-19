import abc

from dcdatabase.phishstorymongo import PhishstoryMongo

from dcumiddleware.urihelper import URIHelper


class Review(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, settings):
        self._db = PhishstoryMongo(settings)
        self._urihelper = URIHelper(settings)

    @abc.abstractmethod
    def place_in_review(self, ticket, hold_time):
        """
        Places a ticket in review until the hold_time
        :param ticket:
        :param hold_time:
        :return:
        """

    def _review_until(self, ticket, field, date):
        """
        Place the specified ticket on hold until the specified date, using the given field
        :param ticket:
        :param field:
        :param hold_until:
        :return:
        """
        data = {field: date}
        return self._db.update_incident(ticket, data)
