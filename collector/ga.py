import base64
import json
import logging
import re

from requests.exceptions import HTTPError
from dateutil import parser
from gapy.client import from_private_key, from_secrets_file
from gapy.error import GapyError
import requests

from collector import load_json, get_credentials
from collector.datetimeutil \
    import to_datetime, period_range, to_utc, a_week_ago
from collector.jsonencoder import JSONEncoder


def _create_client(credentials):
    if "CLIENT_SECRETS" in credentials:
        return from_secrets_file(
            credentials['CLIENT_SECRETS'],
            storage_path=credentials['STORAGE_PATH']

        )
    else:
        return from_private_key(
            credentials['ACCOUNT_NAME'],
            private_key_path=credentials['PRIVATE_KEY'],
            storage_path=credentials['STORAGE_PATH']
        )


def query_ga(client, config, start_date, end_date):
    logging.info("Querying GA for data in the period: %s - %s"
                 % (str(start_date), str(end_date)))

    return client.query.get(
        config["id"].replace("ga:", ""),
        start_date,
        end_date,
        config["metrics"],
        config.get("dimensions"),
        config.get("filters")
    )


def send_data(documents, config):
    if len(documents) == 0:
        logging.info("No data returned with current configuration")
        return
    url = config["url"]
    documents = json.dumps(documents, cls=JSONEncoder, indent=1)
    headers = {
        "Content-type": "application/json",
        "Authorization": "Bearer " + config["token"]
    }

    response = requests.post(url, data=documents, headers=headers)

    logging.info("Received response:\n%s" % response.text)

    response.raise_for_status()


def _format(timestamp):
    return to_utc(timestamp).strftime("%Y%m%d%H%M%S")


def value_id(value):
    value_bytes = value.encode('utf-8')
    logging.debug(u"'{0}' ({1})".format(value, type(value)))
    return base64.urlsafe_b64encode(value_bytes), value_bytes


def data_id(data_type, timestamp, period, dimension_values):
    human_id = "_".join(
        [data_type, _format(timestamp), period] + dimension_values)
    return value_id(human_id)


def map_one_to_one_fields(mapping, pairs):
    return dict(
        [(mapping.get(key, key), value) for key, value in pairs.items()]
    )


def map_multi_value_fields(mapping, pairs):
    multi_value_regexp = '^(.*)_(\d*)$'
    multi_value_delimiter = ':'
    mapped_pairs = {}

    for from_key, to_key in mapping.items():
        multi_value_matches = re.search(multi_value_regexp, from_key)
        if multi_value_matches:
            key = multi_value_matches.group(1)
            index = int(multi_value_matches.group(2))
            multi_value = pairs.get(key)
            if multi_value is None:
                continue

            values = multi_value.split(multi_value_delimiter)
            if index < len(values):
                mapped_pairs[to_key] = values[index]

    return mapped_pairs


def apply_key_mapping(mapping, pairs):
    return dict(map_one_to_one_fields(mapping, pairs).items() +
                map_multi_value_fields(mapping, pairs).items())


def build_document(item, data_type, start_date,
                   mappings=None, idDimension=None):
    if data_type is None:
        raise ValueError("Must provide a data type")
    if mappings is None:
        mappings = {}
    period = "week"

    if idDimension is not None:
        (_id, human_id) = value_id(
            item['dimensions'][idDimension])
    else:
        (_id, human_id) = data_id(
            data_type,
            to_datetime(start_date),
            period,
            item.get('dimensions', {}).values())

    base_properties = {
        "_id": _id,
        "_timestamp": to_datetime(start_date),
        "humanId": human_id,
        "timeSpan": period,
        "dataType": data_type
    }
    dimensions = apply_key_mapping(
        mappings,
        item.get("dimensions", {})).items()
    metrics = [(key, int(value)) for key, value in item["metrics"].items()]
    return dict(base_properties.items() + dimensions + metrics)


def pretty_print(obj):
    return json.dumps(obj, indent=2)


def build_document_set(results, data_type, mappings, idDimension=None):
    return [build_document(item, data_type, start, mappings, idDimension)
            for start, item in results]


def query_for_range(client, query, period_start, period_end):
    items = []
    for start, end in period_range(period_start, period_end):
        items += [
            (start, item) for item in query_ga(client, query, start, end)]

    return items


def query_documents_for(query, credentials, start_date, end_date):
    client = _create_client(credentials)

    mappings = query.get("mappings", {})
    idDimension = query.get("idDimension", None)

    results = query_for_range(client, query["query"], start_date, end_date)

    return build_document_set(results, query["dataType"],
                              mappings, idDimension)


def send_records_for(query, credentials, start_date=None, end_date=None):
    documents = query_documents_for(query, credentials, start_date, end_date)

    send_data(documents, query["target"])
