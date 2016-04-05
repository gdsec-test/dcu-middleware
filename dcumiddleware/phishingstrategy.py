import logging

from dcumiddleware.interfaces.strategy import Strategy


class PhishingStrategy(Strategy):

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def process(self, data, **kwargs):
        super(PhishingStrategy, self).process(data)