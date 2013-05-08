from datetime import timedelta
import base64
import json
import logging
from pprint import pprint

from requests.exceptions import HTTPError
from dateutil import parser
from gapy.client import from_private_key, from_secrets_file
from gapy.error import GapyError
import requests

from backdrop import load_json, get_credentials
from backdrop.collector.datetimeutil \
    import to_datetime, period_range, to_utc, a_week_ago
from backdrop.collector.jsonencoder import JSONEncoder


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
    return client.query.get(
        config["id"].replace("ga:", ""),
        start_date,
        end_date,
        config["metrics"],
        config["dimensions"]
    )


def send_data(data, config):
    url = config["url"]
    data = json.dumps(data, cls=JSONEncoder)
    headers = {
        "Content-type": "application/json",
        "Authorization": "Bearer " + config["token"]
    }

    logging.debug("Posting:\n%s" % data)

    response = requests.post(url, data=data, headers=headers)

    logging.info("Received response:\n%s" % response.text)

    response.raise_for_status()


def _format(timestamp):
    return to_utc(timestamp).strftime("%Y%m%d%H%M%S")


def data_id(data_type, timestamp, period, dimension_values):
    return base64.urlsafe_b64encode("_".join(
        [data_type, _format(timestamp), period] + dimension_values
    ))


def apply_key_mapping(mapping, pairs):
    return dict(
        [ (mapping.get(key, key), value) for key, value in pairs.items()]
    )


def build_document(item, data_type, start_date, end_date, mappings=None):
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


def parse_date(date_string):
    if date_string is not None:
        return parser.parse(date_string).date()


def pretty_print(obj):
    return json.dumps(obj, indent=2)


def run(config_path, start_date=None, end_date=None):
    try:
        config = load_json(config_path)

        logging.info("Configuration (%s): %s"
                     % (config_path, pretty_print(config)))

        # TODO: default dates should depend on the time period
        period_start = parse_date(start_date) or a_week_ago()
        period_end = parse_date(end_date) or a_week_ago()

        logging.info("Querying GA for data in the period: %s - %s"
                     % (str(period_start), str(period_end)))

        credentials = get_credentials()

        client = _create_client(credentials)

        mappings = config.get("mappings", {})

        documents = []

        for start, end in period_range(period_start, period_end):
            response = query_ga(client, config["query"], start, end)

            documents += [
                build_document(item, config["dataType"], start, end, mappings)
                for item in response
            ]

        if any(documents):
            send_data(documents, config["target"])

    except HTTPError:
        logging.exception("Unable to send data to target")
        exit(-3)

    except GapyError:
        logging.exception("Unable to retrieve data from Google Analytics")
        exit(-2)

    except Exception as e:
        logging.exception(e)
        exit(-1)
