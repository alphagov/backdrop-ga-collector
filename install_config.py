import argparse
import json
import os
import re
import shutil


TARGET_URL = "http://write.backdrop.dev.gov.uk/licensing_journey"
TARGET_TOKEN = "licensing_journey-bearer-token"


def is_json(filename):
    return filename.endswith(".json")


def is_json_erb(filename):
    return filename.endswith(".json.erb")


def target_filename(filename):
    m = re.match("(.+\.json)(\.erb)?", filename)
    return m.group(1)


def copy(filename):
    source = os.path.join(source_path, filename)
    output = os.path.join("config", filename)

    print "Writing %s ..." % output

    shutil.copyfile(source, output)


def install_config_template(filename):
    source = os.path.join(source_path, filename)
    output = os.path.join("config", target_filename(filename))

    print "Writing %s ..." % output

    with open(source) as stream:
        config = json.load(stream)

    config["target"]["url"] = TARGET_URL
    config["target"]["token"] = TARGET_TOKEN

    with open(output, 'w') as stream:
        json.dump(config, stream)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Install config files from a source directory')
    parser.add_argument('source_path', metavar='source_path',
                        help='path to dir containing configs to install')
    return parser.parse_args()


args = parse_args()
source_path = args.source_path

copy("credentials.json")

for filename in os.listdir(source_path):
    if is_json_erb(filename):
        install_config_template(filename)

print "Done"
