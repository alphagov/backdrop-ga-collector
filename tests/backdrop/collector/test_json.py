import unittest
from hamcrest import assert_that, is_
from backdrop.collector.jsonencoder import JSONEncoder
from tests.backdrop.collector import dt


class TestEncoder(unittest.TestCase):

    def test_datetime_encoding(self):
        s = JSONEncoder().default(dt(2013, 5, 1, 12, 0, 15, "Europe/London"))
        assert_that(s, is_("2013-05-01T12:00:15+01:00"))