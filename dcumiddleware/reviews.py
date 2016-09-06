import logging

from interfaces.review import Review


class BasicReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(BasicReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time, reason = None):
        self._logger.info("Placing {} in review for {} seconds for {}".format(ticket, hold_time, reason))
        return self._review_until(ticket, 'hold_until', hold_time, 'hold_reason', reason)


class FraudReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(FraudReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time, reason = None):
        self._logger.info("Placing {} in fraud review until {} for {}".format(ticket, hold_time, reason))
        return self._review_until(ticket, 'fraud_hold_until', hold_time, 'fraud_hold_reason', reason)

