from datetime import date, datetime
from hamcrest import assert_that, has_entry, only_contains, is_
import mock
from nose.tools import *
import pytz
from backdrop.collector.ga import query_ga, build_document, period_range


def dt(year, month, day, hours, minutes, seconds, tz):
    _dt = datetime(year, month, day, hours, minutes, seconds)
    return pytz.timezone(tz).localize(_dt)


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


def test_build_document():
    gapy_response = {
        "metrics": {"visits": "12345"},
        "dimensions": {"date": "2013-04-02"}
    }

    data = build_document(gapy_response, date(2013, 4, 1), date(2013, 4, 7))

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

    data = build_document(gapy_response, date(2013, 4, 1), date(2013, 4, 7))

    assert_that(data, has_entry("_start_at",
                                dt(2013, 4, 1, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_end_at",
                                dt(2013, 4, 8, 0, 0, 0, "Europe/London")))
    assert_that(data, has_entry("_period", "week"))
    assert_that(data, has_entry("visits", 12345))
    assert_that(data, has_entry("visitors", 5376))


def test_period_range():

    range = period_range(date(2013, 4, 1), date(2013, 4, 7))
    assert_that(range, only_contains(
        (date(2013, 4, 1), date(2013, 4, 7))
    ))

    another_range = period_range(date(2013, 4, 1), date(2013, 4, 21))
    assert_that(another_range, only_contains(
        (date(2013, 4, 1), date(2013, 4, 7)),
        (date(2013, 4, 8), date(2013, 4, 14)),
        (date(2013, 4, 15), date(2013, 4, 21)),
    ))


def test_period_range_adjusts_dates():
    range = period_range(date(2013, 4, 3), date(2013, 4, 10))
    assert_that(range, only_contains(
        (date(2013, 4, 1), date(2013, 4, 7)),
        (date(2013, 4, 8), date(2013, 4, 14))
    ))


@raises(ValueError)
def test_period_range_fails_when_end_is_before_start():
    list(period_range(date(2013, 4, 8), date(2013, 4, 1)))


def test_period_range_returns_the_containing_week_when_start_equals_end():
    range = period_range(date(2013, 4, 8), date(2013, 4, 8))
    assert_that(range, only_contains(
        (date(2013, 4, 8), date(2013, 4, 14))
    ))
