import logging
import os
import sys

from backdrop.collector import arguments
from backdrop.collector.logging_setup import set_up_logging
from collector.ga import send_records_for


def _extra_fields(argv):
    return {
        'command': ' '.join(argv)
    }


if __name__ == '__main__':
    logfile_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'log')
    set_up_logging('ga_collector', logging.INFO, logfile_path,
                   _extra_fields(sys.argv))

    args = arguments.parse_args('Google Analytics')

    send_records_for(args.query, args.credentials, args.start_at, args.end_at)
