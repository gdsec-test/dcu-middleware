import abc


class PhishstoryDB(object):
    """
    Abstract base class for phishstory database operations
    """
    __metaclass__ = abc.ABCMeta

    PHISHING = "PHISHING"
    MALWARE = "MALWARE"
    NETABUSE = "NETABUSE"

    @abc.abstractmethod
    def get_open_tickets(self, incident_type):
        """
        Returns list of open tickets based on the type
        :param incident_type: the type of incident to search for
        :return:
        """

    @abc.abstractmethod
    def update_incident(self, incident_id, incident_dict):
        """
        Updates an existing incident
        :param incident_id: incident id
        :param incident_dict: dictionary representing key/value pairs to update
        :return:
        """

    @abc.abstractmethod
    def add_new_incident(self, incident_type, incident_dict):
        """
        Adds a new incident to the database for the given type
        :param incident_type: The type of incident to add
        :param incident_dict: Dictionary representation of incident data
        :return:
        """
    @abc.abstractmethod
    def add_crits_data(self, incident_id):
        """
        Adds crits related data to an existing incident
        :param incident_id:
        :return:
        """
    @abc.abstractmethod
    def find_incidents(self, field_dict, and_operator=True):
        """
        Finds arbitrary incidents
        :param field_dict: key/value pairs of fields to find.
        NOTE: AND operator assumed
        :return:
        """
