from datetime import date, datetime
from hamcrest import assert_that, has_entry, only_contains, is_
import mock
from nose.tools import *
import pytz
from backdrop.collector.ga import query_ga, build_document, period_range, data_id, apply_key_mapping
from tests.backdrop.collector import dt


def test_query_ga_with_empty_response():
    config = {
        "id": "ga:123",
        "metrics": ["visits"],
        "dimensions": ["date"]
    }
    client = mock.Mock()
    client.query.get.return_value = []

    response = query_ga(client, config, date(2013, 4, 1), date(2013, 4, 7))

    client.query.get.assert_called_once_with(
        "123",
        date(2013, 4, 1),
        date(2013, 4, 7),
        ["visits"],
        ["date"]
    )

    eq_(response, [])


def test_data_id():
    assert_that(data_id("a", dt(2013, 1, 1, 12, 0, 0, "UTC")), is_("a_20130101120000"))
    assert_that(data_id("a", dt(2013, 6, 1, 12, 0, 0, "Europe/London")), is_("a_20130601110000"))
    assert_that(data_id("a", dt(2013, 8, 15, 12, 0, 0, "Europe/Rome")), is_("a_20130815100000"))


def test_build_document():
    gapy_response = {
        "metrics": {"visits": "12345"},
        "dimensions": {"date": "2013-04-02"}
    }

    data = build_document(gapy_response, "weeklyvisits", date(2013, 4, 1), date(2013, 4, 7))

    assert_that(data, has_entry("_id",
                                "weeklyvisits_20130331230000"))
    assert_that(data, has_entry("dataType", "weeklyvisits"))
    assert_that(data, has_entry("_start_at",
                                dt(2013, 4, 1, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_end_at",
                                dt(2013, 4, 8, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_period", "week"))
    assert_that(data, has_entry("date", "2013-04-02"))
    assert_that(data, has_entry("visits", 12345))


def test_build_document_no_dimensions():
    gapy_response = {
        "metrics": {"visits": "12345", "visitors": "5376"}
    }

    data = build_document(gapy_response, None, date(2013, 4, 1),
                          date(2013, 4, 7))

    assert_that(data, has_entry("_start_at",
                                dt(2013, 4, 1, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_end_at",
                                dt(2013, 4, 8, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_period", "week"))
    assert_that(data, has_entry("visits", 12345))
    assert_that(data, has_entry("visitors", 5376))


def test_key_mappings_are_applied_when_building_documents():
    gapy_response = {
        "metrics": {"visits": "12345"},
        "dimensions": {"date": "2013-04-02"}
    }

    data = build_document(
        gapy_response, "weeklyvisits", date(2013, 4, 1), date(2013, 4, 7),
        {"date": "mydate"})

    assert_that(data, has_entry("_id",
                                "weeklyvisits_20130331230000"))
    assert_that(data, has_entry("dataType", "weeklyvisits"))
    assert_that(data, has_entry("_start_at",
                                dt(2013, 4, 1, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_end_at",
                                dt(2013, 4, 8, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_period", "week"))
    assert_that(data, has_entry("mydate", "2013-04-02"))
    assert_that(data, has_entry("visits", 12345))



def test_apply_key_mapping():
    mapping = {"a": "b"}

    document = apply_key_mapping(mapping, {"a": "foo", "c": "bar"})

    assert_that(document, is_({"b": "foo", "c": "bar"}))
