from datetime import timedelta
import json
import logging

from requests.exceptions import HTTPError
from dateutil import parser
import gapy
import requests

from backdrop import load_json, get_credentials
from backdrop.collector.datetimeutil import to_datetime, period_range, to_utc
from backdrop.collector.jsonencoder import JSONEncoder


logging.basicConfig(level=logging.DEBUG)


def _create_client(credentials):
    return gapy.service_account(
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


def data_id(data_type, timestamp):
    return "%s_%s" % (data_type, to_utc(timestamp).strftime("%Y%m%d%H%M%S"))


def build_document(item, data_type, start_date, end_date):
    base_properties = {
        "_id": data_id(data_type, to_datetime(start_date)),
        "_start_at": to_datetime(start_date),
        "_end_at": to_datetime(end_date + timedelta(days=1)),
        "_period": "week",
        "dataType": data_type
    }
    dimensions = item.get("dimensions", {}).items()
    metrics = [(key, int(value)) for key, value in item["metrics"].items()]
    return dict(base_properties.items() + dimensions + metrics)


def run(config_path, start_date, end_date):
    try:
        config = load_json(config_path)

        start_date = parser.parse(start_date)
        end_date = parser.parse(end_date)

        credentials = get_credentials()

        client = _create_client(credentials)

        documents = []

        for start, end in period_range(start_date, end_date):
            response = query_ga(client, config["query"], start, end)

            documents += [build_document(item, config["dataType"], start, end)
                          for item in response]

        if any(documents):
            send_data(documents, config["target"])

    except HTTPError:
        logging.exception("Unable to send data to target")
        exit(-3)

    except gapy.error.GapyError:
        logging.exception("Unable to retrieve data from Google Analytics")
        exit(-2)

    except Exception as e:
        logging.exception(e)
        exit(-1)
