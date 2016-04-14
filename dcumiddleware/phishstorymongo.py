import datetime
import logging

from dcumiddleware.interfaces.phishstorydb import PhishstoryDB
from mongohelper import MongoHelper


class PhishstoryMongo(PhishstoryDB):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._mongo = MongoHelper(settings)

    def add_crits_data(self, crits_data):
        """
        Adds crits data to an existing incident
        :param crits_data:
        :return:
        """
        screenshot_id = None
        sourcecode_id = None
        try:
            screenshot_id = self._mongo.save_file(crits_data[0])
            sourcecode_id = self._mongo.save_file(crits_data[1])
        except Exception as e:
            self._logger.error("Error saving screenshot/sourcecode {}".format(e.message))
        finally:
            return screenshot_id, sourcecode_id

    def add_new_incident(self, incident_id, incident_dict):
        incident_dict.update(dict(_id=incident_id, phishstory_status="OPEN", created=datetime.datetime.utcnow()))
        return self._mongo.add_incident(incident_dict)

    def get_open_tickets(self, incident_type):
        """
        Gets open/valid tickets
        :param incident_type:
        :return:
        """
        return self._mongo.find_incidents(dict(type=incident_type, phishstory_status="OPEN"))

    def update_incident(self, incident_id, incident_dict):
        """
        Updates the incident with the incident dict and returns the updated document
        :param incident_id:
        :param incident_dict:
        :return:
        """
        incident_dict.update(dict(last_modified=datetime.datetime.utcnow()))
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

    def close_incident(self, incident_id, additonal_data):
        """
        Closes the given incident. Will insert the incident if it doesnt already
        exist
        :param incident_id:
        :return:
        """
        additonal_data.update(dict(phishstory_status="CLOSED", closed=datetime.datetime.utcnow()))
        return self._mongo.update_incident(incident_id, additonal_data, True)
