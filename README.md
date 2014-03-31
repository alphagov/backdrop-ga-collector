# backdrop-ga-collector

[![Build Status](https://travis-ci.org/alphagov/backdrop-ga-collector.png?branch=master)](https://travis-ci.org/alphagov/backdrop-ga-collector?branch=master)


[![Dependency Status](https://gemnasium.com/alphagov/backdrop-ga-collector.png)](https://gemnasium.com/alphagov/backdrop-ga-collector)

Query Google Analytics data and send records to a [backdrop](https://github.com/alphagov/backdrop) bucket.


## Install dependencies

We recommend you use [virtualenv](https://pypi.python.org/pypi/virtualenv) and install dependencies with [pip](https://pypi.python.org/pypi/pip).

```shell
# Create a virtualenv
$ virtualenv ~/.virtualenvs/backdrop-ga-collector
# Activate the virtualenv
$ source ~/.virtualenvs/backdrop-ga-collector/bin/activate
# Install dependencies
$ pip install -r requirements.txt
```

## Set up credentials

Backdrop GA collector expects a file called `config/credentials.json` containing information about the google analytics credentials. This can be in one of two forms based on client secrets or a service account. If you don't know which type you want it's probably best to start with the client secrets method.

### Get your client secret file

- Go to the [Google API Console](https://code.google.com/apis/console) and create a new client ID for an installed application.
- Once created click the *Download JSON* link. This is your client secrets file.

### Generate credentials files

Run `python tools/generate-credentials.py /path/to/client_secret.json`.

This will generate the required credentials files in the `./config` directory.

## Create a config

A config is made up of four parts; the data type, the query, mappings and the target.

```json
{
    "dataType": "govuk_weekly_reach",
    "query": {
        "id": "ga:12345678",
        "metrics": [
            "visits",
            "visitors"
        ],
        "dimensions": [
            "customVarValue1",
            "customVarValue2",
            "eventCategory"
        ],
        "filters": [
            "eventCategory=~^categoryPrefix:"
        ]
    },
    "mappings": {
        "customVarValue1": "slug",
        "customVarValue2": "department",
        "eventCategory_0": "categoryId",
        "eventCategory_1": "categoryLabel"
    },
    "idMapping": "eventCategory",
    "plugins": [
      "ComputeDepartmentKey('customVarValue9')",
      "RemoveKey('customVarValue9')",
      "AggregateKey(aggregate_count('visitors'))"
    ],
    "target": {
        "url": "http://write.backdrop.dev.gov.uk/foo",
        "token": "foo-bearer-token"
    }
}
```

### Data type (`dataType`)

Added to all backdrop records to distinguish them.

### Query (`query`)

A Google Analytics query.

### Mappings (`mappings`)

Allows fields in the google analytics response to be mapped to other fields in the backdrop record.

If a multi value field mapping is specified, the field will be split by the delimiter `:` and mapped accordingly. Example: given the field `key` has the value `foo:bar`, the mapping `key_0` will have the value of `foo` and `key_1` will have the value of `bar`.

### Mapping dimensions as ID (`idMapping`)

Allows you to configure one or more of the dimensions fields as the ID for the row, rather than the auto generated unique ID.

If you provide an array in the idMapping field it will concatinate the values of these dimensions as the key.

### Target (`target`)

The backdrop URL and bearer token that the records will be sent to.

### Plugins (`plugins`)

Plugins are a list of [python expressions](http://docs.python.org/2/reference/expressions.html) (i.e, things that can be the body of a `lambda`) and enable arbitrary transformations to data coming from Google Analytics before it is pushed to backdrop. They are executed in the `backdrop.collector.plugins` namespace.

Plugins reside in the [`backdrop-collector-plugins`](https://github.com/alphagov/backdrop-collector-plugins) repository, and are documented over there.

## Run the config

Install dependencies and run the `collect.py` script passing in the path to the query config file, credentials file, a start date and an end date.

NB. You should probably be doing this in a [virtualenv](https://pypi.python.org/pypi/virtualenv).

```shell
python collect.py --credentials=path/to/credentials.json --query=path/to/config.json --start=2012-12-12 --end=2013-01-12
```
