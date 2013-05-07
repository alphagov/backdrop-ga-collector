from datetime import date, datetime
from hamcrest import assert_that, has_entry, only_contains, is_
import mock
from nose.tools import *
import pytz
from backdrop.collector.ga import query_ga, build_document, period_range, data_id
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
    assert_that(
        data_id("a", dt(2012, 1, 1, 12, 0, 0, "UTC"), "week", ["one", "two"]),
        is_("YV8yMDEyMDEwMTEyMDAwMF93ZWVrX29uZV90d28=")
    )


def test_build_document():
    gapy_response = {
        "metrics": {"visits": "12345"},
        "dimensions": {"date": "2013-04-02"}
    }

    data = build_document(gapy_response, "weeklyvisits", date(2013, 4, 1), date(2013, 4, 7))

    assert_that(data, has_entry("_id",
                                "d2Vla2x5dmlzaXRzXzIwMTMwMzMxMjMwMDAwX3dlZWtfMjAxMy0wNC0wMg=="))
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

    data = build_document(gapy_response,
                          "foo",
                          date(2013, 4, 1),
                          date(2013, 4, 7))

    assert_that(data, has_entry("_start_at",
                                dt(2013, 4, 1, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_end_at",
                                dt(2013, 4, 8, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_period", "week"))
    assert_that(data, has_entry("visits", 12345))
    assert_that(data, has_entry("visitors", 5376))

@raises(ValueError)
def test_build_document_fails_with_no_data_type():
    build_document({}, None, date(2012, 12, 12), date(2012, 12, 13))
