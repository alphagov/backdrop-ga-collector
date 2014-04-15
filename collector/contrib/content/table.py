from backdrop.collector.plugins.department import try_get_department

from collector.ga import _create_client, query_documents_for, send_data
from collector.jsonencoder import JSONEncoder

import os


def main(args):
    client = _create_client(args.credentials)

    query = args.query

    assert "filtersets" in query, "`filtersets` must be specified"

    documents = []

    original_filters = query["query"].get("filters", [])

    from pprint import pprint

    for filters in query["filtersets"]:
        print "Query:", filters
        query["query"]["filters"] = original_filters + filters

        pprint(query)

        for f in filters:
            if f.startswith("customVarValue9=~^"):
                department = try_get_department(f[len("customVarValue9=~^"):])
                break
        else:
            # If no matches, raise a RuntimeError
            raise RuntimeError("department not found in filters, expected "
                               "filter expression beginning "
                               "'customVarValue9=~^'.")

        query.setdefault("additionalFields", {}).update(
            {"department": department})

        ds = query_documents_for(client, query, args.start_at, args.end_at)

        documents.extend(ds)

    # from pprint import pprint
    # pprint(documents)

    # return

    # documents =

    # print len(documents)
    # from pprint import pprint
    # from json import dumps

    # print(dumps(documents, cls=JSONEncoder, indent=1))


    send_data(documents, query["target"])
