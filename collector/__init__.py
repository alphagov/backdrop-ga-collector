import json
import os


def path_from_base(*parts):
    return os.path.join(
        os.path.dirname(__file__),
        '..', *parts
    )


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_credentials():
    return load_json(path_from_base('config', 'credentials.json'))
