
class Incident(object):
    """
    Basic class to hold data representing Incidents. This class models the data that will
    be held in MongoDB. As such, the attributes are not pre-determined. NOTE: This
    class is not meant to hold nested documents
    """

    def __init__(self, entries):
        """
        Construct an incident from key value pairs
        :param entries:
        :return:
        """
        self.__dict__.update(**entries)

    def as_dict(self):
        """
        Returns a dictionary representation of the Incident
        :return:
        """
        return self.__dict__

    def __getattr__(self, item):
        """
        Avoid raising an exception if the attribute doesnt exist
        :param item:
        :return:
        """
        return self.__dict__.get(item)

    def __repr__(self):
        return '<\n %s\n>' % str('\n '.join('%s : %s' % (k, repr(v)) for (k, v) in self.__dict__.iteritems()))
