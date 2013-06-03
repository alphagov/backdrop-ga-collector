# backdrop-ga-collector

Query Google Analytics data and send records to a [backdrop](https://github.com/alphagov/backdrop) bucket.


## Set up credentials

Backdrop GA collector expects a file called `config/credentials.json` containing information about the google analytics credentials. This can be in one of two forms based on client secrets or a service account. If you don't know which type you want it's probably best to start with the client secrets method.

### Get your client secrets file

- Go to the [Google API Console](https://code.google.com/apis/console) and create a new client ID for an installed application.
- Once created click the *Download JSON* link. This is your client secrets file.

### Create your credentials file
- Copy `config/credentials-clientsecrets-example.json` to `config/credentials.json`.
- Replace the `/path/to/client_secrets.json` with the path to your newly downloaded client secrets file.
- Replace the `/path/to/storage.db` with a path to a file that will be created to store the refresh token.


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
        "customVarValue2": "department"
    },
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

### Target (`target`)

The backdrop URL and bearer token that the records will be sent to.


## Run the config

Install dependencies and run the `run.py` script passing in the path to the config file, a start date and an end date.

NB. You should probably be doing this in a [virtualenv](https://pypi.python.org/pypi/virtualenv).

```shell
pip install -r requirements.txt
python run.py path/to/config.json 2012-12-12 2013-01-12
```
