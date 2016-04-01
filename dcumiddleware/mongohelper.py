import logging

import gridfs
import pymongo


class MongoHelper:
    """
    This class houses low level database functionality for PhishstoryDB.
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
            iid = iid.inserted_id or None
        except Exception as e:
            self._logger.error("Unable to add incident to database {}".format(e.message))
        finally:
            return iid

    def replace_incident(self, iid, incident):
        """
        Replaces the incident
        :param iid:
        :param incident:
        :return:
        """
        self._logger.info("Replacing incident: {}".format(iid))
        document = None
        try:
            document = self._collection.find_one_and_replace({'_id': iid}, incident)
        except Exception as e:
            self._logger.error("Unable to replace incident {} {}".format(iid, e.message))
        finally:
            return document

    def update_incident(self, iid, update):
        """
        Updates the incident
        :param iid:
        :param incident:
        :return:
        """
        self._logger.info("Updating incident: {}".format(iid))
        document = None
        try:
            document = self._collection.find_one_and_update({'_id': iid}, {'$set':update})
        except Exception as e:
            self._logger.error("Unable to update incident {} {}".format(iid, e.message))
        finally:
            return document

    def find_incident(self, query):
        """
        Finds the given incident by id
        :param query:
        :return:
        """
        document = None
        try:
            document = self._collection.find_one(query)
        except Exception as e:
            self._logger.warning("Unable to find incident {}".format(e.message))
        finally:
            return document

    def find_incidents(self, query):
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

    def save_file(self, dbytes, **kwargs):
        """
        Saves the given bytes to the gridFS. Any additional metadata may be added to the record via the kwargs argument
        :param dbytes:
        :param kwargs:
        :return:
        """
        with self._gridfs.new_file(**kwargs) as fp:
            fp.write(dbytes)
            return fp._id

    def get_file(self, iid):
        """
        Returns the file document, and the raw bytes for the file with the given id
        :param iid:
        :return:
        """
        with self._gridfs.get(iid) as fs_read:
            return fs_read._file, fs_read.read()