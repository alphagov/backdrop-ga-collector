from datetime import date
from hamcrest import assert_that, is_, has_entries, has_item, equal_to
import mock
from nose.tools import *
from collector.ga import query_ga, build_document, data_id, apply_key_mapping, build_document_set, query_for_range, map_multi_value_fields
from tests.collector import dt


def test_query_ga_with_empty_response():
    config = {
        "id": "ga:123",
        "metrics": ["visits"],
        "dimensions": ["date"],
        "filters": ["some-filter"]
    }
    client = mock.Mock()
    client.query.get.return_value = []

    response = query_ga(client, config, date(2013, 4, 1), date(2013, 4, 7))

    client.query.get.assert_called_once_with(
        "123",
        date(2013, 4, 1),
        date(2013, 4, 7),
        ["visits"],
        ["date"],
        ["some-filter"]
    )

    eq_(response, [])


def test_filters_are_optional():
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
        ["date"],
        None
    )

    eq_(response, [])


def test_query_for_range():
    client = mock.Mock()
    query = {
        "id": "12345",
        "metrics": ["visits", "visitors"],
        "dimensions": ["dimension1", "dimension2"],
    }
    response = {
        "visits": "1234",
        "visitors": "321",
        "dimension1": "value1",
        "dimension2": "value2",
    }
    client.query.get.return_value = [response]

    items = query_for_range(client, query, date(2013, 4, 1), date(2013, 4, 8))

    assert_that(len(items), is_(2))

    assert_that(items[0][0], is_(date(2013, 4, 1)))
    assert_that(items[0][1], equal_to(response))

    assert_that(items[1][0], is_(date(2013, 4, 8)))
    assert_that(items[1][1], equal_to(response))


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

    data = build_document(gapy_response, "weeklyvisits", date(2013, 4, 1))

    assert_that(data, has_entries({
        "_id": "d2Vla2x5dmlzaXRzXzIwMTMwMzMxMjMwMDAwX3dlZWtfMjAxMy0wNC0wMg==",
        "dataType": "weeklyvisits",
        "_timestamp": dt(2013, 4, 1, 0, 0, 0, "Europe/London"),
        "timeSpan": "week",
        "date": "2013-04-02",
        "visits": 12345,
    }))


def test_build_document_no_dimensions():
    gapy_response = {
        "metrics": {"visits": "12345", "visitors": "5376"}
    }

    data = build_document(gapy_response, "foo", date(2013, 4, 1))

    assert_that(data, has_entries({
        "_timestamp": dt(2013, 4, 1, 0, 0, 0, "Europe/London"),
        "timeSpan": "week",
        "visits": 12345,
        "visitors": 5376,
    }))


def test_build_document_mappings_are_applied_to_dimensions():
    mappings = {
        "customVarValue1": "name"
    }
    gapy_response = {
        "metrics": {"visits": "12345"},
        "dimensions": {"customVarValue1": "Jane"},
    }

    doc = build_document(gapy_response, "people", date(2013, 4, 1), mappings)

    assert_that(doc, has_entries({
        "name": "Jane"
    }))


def test_build_document_with_multi_value_field_mappings():
    mappings = {
        "multiValuesField": "originalField",
        "multiValuesField_0": "first",
        "multiValuesField_1": "second",
        "multiValuesField_2": "third",
    }

    gapy_response = {
        "metrics": {"visits": "12345"},
        "dimensions": {"multiValuesField": "first value:second value:third value"}
    }

    doc = build_document(gapy_response, "multival", date(2013, 4, 1), mappings)

    assert_that(doc, has_entries({
        "originalField": "first value:second value:third value",
        "first": "first value",
        "second": "second value",
        "third": "third value",
    }))


def test_apply_key_mapping():
    mapping = {"a": "b"}

    document = apply_key_mapping(mapping, {"a": "foo", "c": "bar"})

    assert_that(document, is_({"b": "foo", "c": "bar"}))


def test_map_available_multi_value_fields():
    mapping = {
        'key_0': 'one',
        'key_1': 'two',
        'key_2': 'not_in_value',
        'no_key_0': 'dont_exist'
    }

    document = map_multi_value_fields(mapping, {'key': 'foo:bar'})

    assert_that(document, is_({'one': 'foo', 'two': 'bar'}))


def test_build_document_set():
    def build_gapy_response(visits, name):
        return {
            "metrics": {"visits": visits},
            "dimensions": {"customVarValue1": name}
        }

    mappings = {
        "customVarValue1": "name"
    }
    results = [
        (date(2013, 4, 1), build_gapy_response("12345", "Jane")),
        (date(2013, 4, 1), build_gapy_response("2313", "John")),
        (date(2013, 4, 8), build_gapy_response("4323", "Joanne"))
    ]
    docs = build_document_set(results, "people", mappings)

    assert_that(docs, has_item(has_entries({
        "name": "Jane",
        "_timestamp": dt(2013, 4, 1, 0, 0, 0, "Europe/London"),
        "dataType": "people",
        "visits": 12345,
    })))
    assert_that(docs, has_item(has_entries({
        "name": "John",
        "_timestamp": dt(2013, 4, 1, 0, 0, 0, "Europe/London"),
        "visits": 2313,
    })))
    assert_that(docs, has_item(has_entries({
        "name": "Joanne",
        "_timestamp": dt(2013, 4, 8, 0, 0, 0, "Europe/London"),
        "visits": 4323,
    })))


@raises(ValueError)
def test_build_document_fails_with_no_data_type():
    build_document({}, None, date(2012, 12, 12))
