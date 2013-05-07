from datetime import datetime, time, timedelta, date
import pytz


GB_TIMEZONE = pytz.timezone("Europe/London")

MONDAY = 0


def to_datetime(a_date):
    return GB_TIMEZONE.localize(datetime.combine(a_date, time(0)))


def to_utc(a_datetime):
    return a_datetime.astimezone(pytz.UTC)


def period_range(start_date, end_date):
    if start_date > end_date:
        raise ValueError

    if start_date.weekday != MONDAY:
        start_date = start_date - timedelta(days=start_date.weekday())

    period = timedelta(days=7)
    while start_date <= end_date:
        yield (start_date, start_date + timedelta(days=6))
        start_date += period


def a_week_ago():
    return date.today() - timedelta(days=7)
