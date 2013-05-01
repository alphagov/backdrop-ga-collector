from datetime import time, timedelta, datetime
from dateutil import parser
import gapy
import pytz
from backdrop import load_json, get_credentials


TIMEZONE = pytz.timezone("Europe/London")


def _create_client():
    credentials = get_credentials()

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


def send_data(data):
    for datum in data:
        print datum


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

    client = _create_client()

    response = query_ga(client, config, start_date, end_date)

    documents = [ build_document(item, start_date, end_date) for item in response ]

    send_data(documents)
