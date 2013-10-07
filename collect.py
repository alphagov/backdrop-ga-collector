from backdrop.collector import arguments
from collector.ga import send_records_for

if __name__ == '__main__':
    args = arguments.parse_args('Google Analytics')

    send_records_for(args.query, args.credentials, args.start_at, args.end_at)
