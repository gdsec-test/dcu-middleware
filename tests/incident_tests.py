from dcumiddleware.incident import Incident
from nose.tools import assert_true, assert_false


class TestIncident:

    def test_create_incident(self):
        inc = Incident(dict(name="test", value=1234))
        assert_true(len(inc.__dict__) > 0)

    def test_as_dict(self):
        di = dict(name="test", value=1234)
        inc = Incident(di)
        assert_true(inc.as_dict() == di)

    def test_get_value(self):
        di = dict(name="test", value=1234)
        inc = Incident(di)
        assert_true(inc.name == 'test')
        assert_true(inc.value==1234)
        assert_false(inc.blah)

    def test_new_field(self):
        di = dict(name="test", value=1234)
        inc = Incident(di)
        inc.value1 = 12345
        assert_true(inc.value1 == 12345)
