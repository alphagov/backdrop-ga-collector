import logging

from backdrop.collector import arguments
from backdrop.collector.logging_setup import set_up_logging
from collector.ga import send_records_for

if __name__ == '__main__':
    set_up_logging('ga_collector', logging.DEBUG)

    args = arguments.parse_args('Google Analytics')

    send_records_for(args.query, args.credentials, args.start_at, args.end_at)
