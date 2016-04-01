import logging
from phishstorydb import PhishstoryDB
from mongohelper import MongoHelper


class PhishstoryMongo(PhishstoryDB):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._mongo = MongoHelper(settings)

    def add_crits_data(self, incident_id):
        """TODO """

    def add_new_incident(self, incident_type, incident_dict):
        incident_dict.update(dict(type=incident_type))
        self._mongo.add_incident(incident_dict)

    def get_open_tickets(self, incident_type):
        return self._mongo.find_incidents(dict(type=incident_type))

    def update_incident(self, incident_id, incident_dict):
        """TODO """
