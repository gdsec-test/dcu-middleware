import logging
from datetime import datetime, timedelta

from interfaces.review import Suspend


class BasicReview(Suspend):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(BasicReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time):
        self._logger.info("Placing {} in review for {} seconds".format(ticket, hold_time))
        return self._review_until(ticket, datetime.utcnow() + timedelta(seconds=hold_time))


class FraudReview(Suspend):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(FraudReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time):
        """
        Places the ticket in review for the specified hold time, if no other open ticket for that
        domain is currently in review. If another ticket for that domain is found to be in review, and
        not expired, then the review time for the existing ticket is used for the ticket.
        :param ticket:
        :param hold_time:
        :return:
        """
        doc = self._db.get_incident(ticket)
        if doc:
            query = dict(phishstory_status='OPEN', sourceDomainOrIp=doc['sourceDomainOrIp'],
                         hold_until={'$exists': True})
            domain_ticket = self._db.find_incidents(query, [('hold_until', 1)], 1)
            hold_until = datetime.utcnow() + timedelta(seconds=hold_time)
            additional_data = dict(fraud_notified=True)
            if domain_ticket and domain_ticket[0]['hold_until'] > datetime.utcnow():
                hold_until = domain_ticket[0]['hold_until']
                additional_data = dict()
            self._logger.info("Placing {} in review until {}".format(ticket, hold_until))
            return self._review_until(ticket, hold_until, additional_data)
        else:
            self._logger.error("No such incident {}".format(ticket))

