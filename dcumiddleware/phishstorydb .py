import logging

import gridfs
import pymongo


class PhishstoryDB:
    """
    This class houses the database functionality for PhishstoryDB.
    """
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._conn = pymongo.MongoClient(settings.DBHOST, settings.DBPORT)
        self._db = self._conn[settings.DB]
        self._collection = self._db[settings.COLLECTION]
        self._gridfs = gridfs.GridFS(self._db)

    def add_incident(self, incident):
        """
        Adds an incident to the database
        :param incident:
        :return:
        """
        self._logger.info("Adding incident: {}".format(incident))
        iid = None
        try:
            iid = self._collection.insert_one(incident)
        except Exception as e:
            self._logger.error("Unable to add incident to database {}".format(e.message))
        finally:
            return iid

    def replace_incident(self, id, incident):
        """
        Replaces the incident
        :param id:
        :param incident:
        :return:
        """
        self._logger.info("Updating incident: {}".format(id))
        document = None
        try:
            document = self._collection.find_one_and_replace({'_id': id}, incident)
        except Exception as e:
            self._logger.error("Unable to update incident {} {}".format(id, e.message))
        finally:
            return document

    def find_incident(self, id):
        """
        Finds the given incident by id
        :param id:
        :return:
        """
        document = None
        try:
            document = self._collection.find_one({'_id': id})
        except Exception as e:
            self._logger.warning("Unable to find incident {} {}".format(id, e.message))
        finally:
            return document

    def _find_incidents(self, query):
        """
        Find incidents given a query(dictionary)
        :param query:
        :return:
        """
        document_list = None
        try:
            document_list = self._collection.find(query)
        except Exception as e:
            self._logger.warning("Unable to find incidents {}".format(id, e.message))
        finally:
            return document_list

    def save_file(self, bytes, **kwargs):
        """
        Saves the given bytes to the gridFS. Any additional metadata may be added to the record via the kwargs argument
        :param bytes:
        :param kwargs:
        :return:
        """
        with self._gridfs.new_file(**kwargs) as fp:
            fp.write(bytes)
            return fp._id

    def get_file(self, id):
        """
        Returns the raw bytes for the file with the given id
        :param id:
        :return:
        """
        with self._gridfs.get(id) as fs_read:
            return fs_read._file, fs_read.read()
