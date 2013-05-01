from datetime import time, timedelta, datetime
from dateutil import parser
import gapy
import pytz
import requests
import json
from backdrop import load_json, get_credentials


TIMEZONE = pytz.timezone("Europe/London")


class MyEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return str(obj.timetuple())

        return json.JSONEncoder.default(self, obj)


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
    for datum in data:
        print datum

    r = requests.post(
        config["url"],
        data=json.dumps(data, cls=MyEncoder),
        headers={"Authorization": "Bearer " + config["token"]}
    )
    
    print r.status_code


def _to_datetime(start_date):
    return TIMEZONE.localize(datetime.combine(start_date, time(0)))


def _period_properties(end_date, start_date):
    return {
        "_start_at": _to_datetime(start_date),
        "_end_at": _to_datetime(end_date + timedelta(days=1)),
        "_period": "week"
    }


def build_document(item, start_date, end_date):
    period_properties = _period_properties(end_date, start_date).items()
    dimensions = item.get("dimensions", {}).items()
    metrics = [(key, int(value)) for key, value in item["metrics"].items()]
    return dict( period_properties + dimensions + metrics )


def run(config_path, start_date, end_date):
    config = load_json(config_path)

    start_date = parser.parse(start_date)
    end_date = parser.parse(end_date)

    credentials = get_credentials()

    client = _create_client(credentials)

    response = query_ga(client, config["query"], start_date, end_date)

    documents = [ build_document(item, start_date, end_date) for item in response ]

    send_data(documents, config["target"])
