import base64
import json
import logging
import re

from gapy.client import from_private_key, from_secrets_file
import requests

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

    # If maxResults is 0, don't include it in the query.
    # Same for a sort == [].

    maxResults = config.get("maxResults", None)
    if maxResults == 0:
        maxResults = None

    sort = config.get("sort", None)
    if sort == []:
        sort = None

    return client.query.get(
        config["id"].replace("ga:", ""),
        start_date,
        end_date,
        config["metrics"],
        config.get("dimensions"),
        config.get("filters"),
        maxResults,
        sort,
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
    # `dimension_values` may be non-string python types and need to be coerced.
    values = map(unicode, dimension_values)
    slugs = [data_type, _format(timestamp), period] + values
    return value_id("_".join(slugs))


def map_one_to_one_fields(mapping, pairs):
    return dict((mapping.get(key, key), value) for key, value in pairs.items())


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


def try_number(value):
    """
    Attempt to cast the string `value` to an int, and failing that, a float,
    failing that, raise a ValueError.
    """

    for cast_function in [int, float]:
        try:
            return cast_function(value)
        except ValueError:
            pass

    raise ValueError("Unable to use value as int or float: {0!r}"
                     .format(value))


def build_document(item, data_type,
                   mappings=None, idMapping=None):
    if data_type is None:
        raise ValueError("Must provide a data type")
    if mappings is None:
        mappings = {}
    period = "week"

    if idMapping is not None:
        if isinstance(idMapping, list):
            values_for_id = map(lambda d: item['dimensions'][d], idMapping)
            value_for_id = "".join(values_for_id)
        else:
            value_for_id = item['dimensions'][idMapping]

        (_id, human_id) = value_id(value_for_id)
    else:
        (_id, human_id) = data_id(
            data_type,
            to_datetime(item["start_date"]),
            period,
            item.get('dimensions', {}).values())

    base_properties = {
        "_id": _id,
        "_timestamp": to_datetime(item["start_date"]),
        "humanId": human_id,
        "timeSpan": period,
        "dataType": data_type
    }
    dimensions = apply_key_mapping(
        mappings,
        item.get("dimensions", {})).items()

    metrics = [(key, try_number(value))
               for key, value in item["metrics"].items()]
    return dict(base_properties.items() + dimensions + metrics)


def pretty_print(obj):
    return json.dumps(obj, indent=2)


def build_document_set(results, data_type, mappings, idMapping=None):
    return [build_document(item, data_type, mappings, idMapping)
            for item in results]


def query_for_range(client, query, period_start, period_end):
    items = []
    extend = items.extend

    for start, end in period_range(period_start, period_end):
        extend(query_ga(client, query, start, end))

    return items


def run_plugins(plugins_strings, results):

    last_plugin = plugins_strings[-1]
    if not last_plugin.startswith("ComputeIdFrom"):
        raise RuntimeError("Last plugin must be `ComputeIdFrom` for now. This "
                           "may be changed with further development if "
                           "necessary")

    # Import is here so that it is only required when "plugins" is specified
    from backdrop.collector.plugins import load_plugins
    plugins = load_plugins(plugins_strings)

    # Plugins are designed so that their configuration is described in the
    # plugin string. At this point, `plugin` should be a closure which only
    # requires the documents to process.
    for plugin in plugins:
        results = plugin(results)

    return results


def query_documents_for(client, query, start_date, end_date):
    results = query_for_range(client, query["query"], start_date, end_date)

    mappings = query.get("mappings", {})
    idMapping = query.get("idMapping", None)

    docs = build_document_set(results, query["dataType"], mappings, idMapping)

    if "additionalFields" in query:
        additional_fields = query["additionalFields"]
        for doc in docs:
            doc.update(additional_fields)

    if "plugins" in query:
        docs = run_plugins(query["plugins"], docs)

    return docs


def send_records_for(query, credentials, start_date=None, end_date=None):
    client = _create_client(credentials)

    documents = query_documents_for(client, query, start_date, end_date)

    send_data(documents, query["target"])
