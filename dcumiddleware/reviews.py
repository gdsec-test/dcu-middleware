import logging

from interfaces.review import Review


class BasicReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(BasicReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time):
        self._logger.info("Placing {} in review for {} seconds".format(ticket, hold_time))
        return self._review_until(ticket, 'hold_until', hold_time)


class FraudReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(FraudReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time):
        self._logger.info("Placing {} in fraud review until {}".format(ticket, hold_time))
        return self._review_until(ticket, 'fraud_hold_until', hold_time)

