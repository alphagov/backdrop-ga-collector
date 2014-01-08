import logging
import os

from backdrop.collector import arguments
from backdrop.collector.logging_setup import set_up_logging
from collector.ga import send_records_for

if __name__ == '__main__':
    logfile_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'log')
    set_up_logging('ga_collector', logging.DEBUG, logfile_path)

    args = arguments.parse_args('Google Analytics')

    send_records_for(args.query, args.credentials, args.start_at, args.end_at)
