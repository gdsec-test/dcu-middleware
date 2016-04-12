import logging

from dcumiddleware.interfaces.phishstorydb import PhishstoryDB
from mongohelper import MongoHelper


class PhishstoryMongo(PhishstoryDB):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._mongo = MongoHelper(settings)

    def add_crits_data(self, incident_id, crits_data):
        """
        Adds crits data to an existing incident
        :param incident_id:
        :param crits_data:
        :return:
        """
        document = None
        try:
            screenshot_id = self._mongo.save_file(crits_data[0])
            sourcecode_id = self._mongo.save_file(crits_data[1])
            incident_dict = {'screenshot_id': screenshot_id, 'sourcecode_id': sourcecode_id}
            document = self._mongo.update_incident(incident_id, incident_dict)
        except Exception as e:
            self._logger.error("Error saving screenshot/sourcecode for incident id {}:{}".format(incident_id, e.message))
        finally:
            return document

    def add_new_incident(self, incident_id, incident_dict):
        incident_dict.update(dict(_id=incident_id))
        self._mongo.add_incident(incident_dict)

    def get_open_tickets(self, incident_type):
        """
        Gets open/valid tickets
        :param incident_type:
        :return:
        """
        return self._mongo.find_incidents(dict(type=incident_type, valid=True))

    def update_incident(self, incident_id, incident_dict):
        """
        Updates the incident with the incident dict and returns the updated document
        :param incident_id:
        :param incident_dict:
        :return:
        """
        document = self._mongo.update_incident(incident_id, incident_dict)
        return document

    def get_incident(self, incident_id):
        """
        Returns the given incident
        :param incident_id:
        :return:
        """
        return self._mongo.find_incident(dict(_id=incident_id))

    def get_crits_data(self, incident_id):
        """
        Returns a tuple of the screenshot, and sourcecode associated with the incident
        :param incident_id:
        :return:
        """
        screenshot = None
        sourcecode = None
        document = self.get_incident(incident_id)
        if document:
            if 'screenshot_id' in document:
                screenshot = self._mongo.get_file(document['screenshot_id'])
            if 'sourcecode_id' in document:
                sourcecode = self._mongo.get_file(document['sourcecode_id'])
        return screenshot, sourcecode
