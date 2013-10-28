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


logging.basicConfig(level=logging.DEBUG)


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
        config["dimensions"],
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


def data_id(data_type, timestamp, period, dimension_values):
    return base64.urlsafe_b64encode("_".join(
        [data_type, _format(timestamp), period] + dimension_values
    ))


def apply_multi_value_fields_mapping(mapping, pairs):
    multi_value_regexp = '(.*)_(\d)'
    multi_value_delimiter = ':'

    for from_key, to_key in mapping.items():
        multi_value_mapping = re.search(multi_value_regexp, from_key)
        if multi_value_mapping:
            key, index = multi_value_mapping.groups()
            value = pairs[key]
            pairs[to_key] = value.split(multi_value_delimiter)[int(index)]
    return pairs


def apply_key_mapping(mapping, pairs):
    mapped_pairs = dict(
        [(mapping.get(key, key), value) for key, value in pairs.items()]
    )
    return apply_multi_value_fields_mapping(mapping, mapped_pairs)


def build_document(item, data_type, start_date, mappings=None):
    if data_type is None:
        raise ValueError("Must provide a data type")
    if mappings is None:
        mappings = {}
    period = "week"
    base_properties = {
        "_id": data_id(
            data_type, to_datetime(start_date), period,
            item.get("dimensions", {}).values()
        ),
        "_timestamp": to_datetime(start_date),
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


def build_document_set(results, data_type, mappings):
    return [build_document(item, data_type, start, mappings)
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

    results = query_for_range(client, query["query"], start_date, end_date)

    return build_document_set(results, query["dataType"], mappings)


def send_records_for(query, credentials, start_date=None, end_date=None):
    documents = query_documents_for(query, credentials, start_date, end_date)

    send_data(documents, query["target"])
