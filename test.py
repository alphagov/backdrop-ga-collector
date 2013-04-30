from datetime import datetime, timedelta
import json
from dateutil.relativedelta import relativedelta, MO
import gapy
import sys
from dateutil import parser


ACCOUNT_NAME = "143024816192-n2ie23t8lg6o9s4sd8bgnjhv5nk7h5pm.apps.googleusercontent.com"
STORAGE_PATH = "/var/lib/govuk/backdrop/backdrop-ga-collector.storage.db"
PRIVATE_KEY = "/var/lib/govuk/backdrop/private-key"


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def period_range(start, stop, period):
    while start < stop:
        yield(start, start + period)
        start += period


def weekly_visits(client, start_date, end_date):
    pass


if __name__ == "__main__":
    start_date = parser.parse(sys.argv[1]) + relativedelta(weekday=MO(-1))
    end_date = parser.parse(sys.argv[2]) + relativedelta(weekday=MO(+1))


    client = gapy.service_account(
        "143024816192-n2ie23t8lg6o9s4sd8bgnjhv5nk7h5pm.apps.googleusercontent.com",
        private_key_path="privatekey",
        storage_path="/var/lib/backdrop-ga-collector.storage.db"
    )


    for start_date, end_date in period_range(start_date, end_date, timedelta(days=7)):
        data = client.query.get(
            "53872948",
            start_date,
            end_date - timedelta(days=1),
            ["visits"],
        )
        for datum in data:
            print(json.dumps({
                "_start_at": start_date,
                "_end_at": end_date,
                "_period": "week",
                "visits": int(datum['metrics']['visits'])
            }, cls=JsonEncoder))




# python get_data.py -f licensing_weekly_success.json 2012-12-12 2013-02-02

# {
#   id: 53872948
#   metrics
#   dimensions
#   filters
# }