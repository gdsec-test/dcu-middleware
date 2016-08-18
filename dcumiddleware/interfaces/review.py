import abc

from dcdatabase.phishstorymongo import PhishstoryMongo


class Suspend(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, settings):
        self._db = PhishstoryMongo(settings)

    @abc.abstractmethod
    def place_in_review(self, ticket, hold_time):
        """
        Places a ticket in review for the specified number of seconds
        :param ticket:
        :param hold_time:
        :return:
        """

    def _review_until(self, ticket, hold_until, meta_data=None):
        """
        Place the given incident in review until the specified date
        :param data:
        :return:
        """
        data = dict(hold_until=hold_until)
        if meta_data:
            data.update(meta_data)
        return self._db.update_incident(ticket, data)
