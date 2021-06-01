import argparse
import logging
import os
import sys
import time


from functools import partial
from typing import Iterable, Optional


try:
    from ..src.postgres_wrapper import WebMonitoringDBWrapper
    from ..src.consumer import Consumer
    from ..utils.env_config import config
except ImportError:
    from src.postgres_wrapper import WebMonitoringDBWrapper
    from src.consumer import Consumer
    from utils.env_config import config


TOPIC = 'website-metrics'
SCHEMA = 'website_metrics'

_storage_provider = os.environ['STORAGE_SERVICE_PROVIDER']
_storage_settings = config['Metrics storage endpoint'][_storage_provider]
_db_settings = _storage_settings['db']

_db_auth_basic = (os.environ.get('DB_LOGIN'), os.environ.get('DB_PASS'))

SLEEP_BETWEEN_REQUESTS = _storage_settings['upload every']

_collection_provider = os.environ['BROKER_SERVICE_PROVIDER']
_broker_settings = config['Metrics collection endpoint'][_collection_provider]['broker']
_broker_type = _broker_settings['type']
_broker_url = _broker_settings['host']
_broker_port = str(_broker_settings['port'])
_broker_uri = ':'.join((_broker_url, _broker_port))

_broker_auth_sasl_plain = {
    'sasl_mechanism': 'PLAIN',
    'sasl_plain_username': os.environ.get('BROKER_USERNAME'),
    'sasl_plain_password': os.environ.get('BROKER_PASSWORD')
}

_broker_auth_cert = {
    'ca_path': os.environ.get('BROKER_CA_CERT'),
    'cert_path': os.environ.get('BROKER_SERVICE_CERT'),
    'key_path': os.environ.get('BROKER_SERVICE_KEY')
}


_brokers = {
    'kafka': Consumer
}

_db = {
    'postgres': WebMonitoringDBWrapper
}

_broker_auth = {
    'sasl_plain': _broker_auth_sasl_plain,
    'client_cert': _broker_auth_cert
}

_db_auth = {
    'basic': _db_auth_basic
}

CONSUMER = _brokers[_broker_settings['type']](
    TOPIC,
    service_uri=_broker_uri,
    **_broker_auth[_broker_settings['auth']]
)

if isinstance(_db_auth[_db_settings['auth']], tuple):
    DATABASE = partial(
        _db[_db_settings['type']],
        _db_settings['host'],
        _db_settings['port'],
        *_db_auth[_db_settings['auth']]
    )
elif isinstance(_db_auth[_db_settings['auth']], dict):
    DATABASE = partial(
        _db[_db_settings['type']],
        _db_settings['host'],
        _db_settings['port'],
        **_db_auth[_db_settings['auth']]
    )
else:
    msg = f'Database auth object have improper type. Got {type(_db_auth[_db_settings["auth"]])}'
    raise ValueError(f'{msg}, expected: tuple or dict')


def consume_publish_run(
        consumer,
        db_wrapper,
        sleep_time: int,
        topics: Optional[Iterable[str]] = None,
        cycles: Optional[int] = None
):
    """Service runner for fetching data from Kafka broker and posting to DB

    Args:
        consumer: Kafka consumer
        db_wrapper: helper lib to work with DB
        sleep_time: number of seconds to wait between metric collection
        topics: to change to. When provided, previous topics are wiped out
        cycles: number of iterations to run the service. Runs infinitely if None

    Returns:
        None, runs until interrupted by user or iterated "iterations" times

    """

    if topics:
        consumer.change_topics(topics)
    log = logging.getLogger('ConsumerAndSharingService')
    log.addHandler(logging.NullHandler())

    with consumer:
        counter = 0
        def proceed(): return counter < cycles if cycles else True
        while True:
            data = consumer.fetch_latest()
            if not data:
                log.warning('No data to push to DB. Is web metric service running?')
            else:
                log.info(f'Successfully fetched {len(data)} pieces of data')
                db_wrapper.insert(data)
            counter += 1
            if not proceed():
                log.info(f'Exiting service because it worked {counter} out of {cycles} cycles')
                break
            time.sleep(sleep_time)
    sys.exit(0)


if __name__ == '__main__':
    cmd_args = argparse.ArgumentParser()

    cmd_args.add_argument(
        '--topic',
        dest='topic',
        help=f'topic name to publish, no quotes. Defaults to {TOPIC}',
        default=TOPIC,
        type=str
    )
    cmd_args.add_argument(
        '--schema',
        dest='schema',
        help=f'Database schema to store, no quotes. Defaults to {SCHEMA}',
        default=SCHEMA,
        type=str
    )
    cmd_args.add_argument(
        '--cycles',
        dest='cycles',
        help='number of cycles to run, infinite if not specified',
        type=int
    )
    cmd_args.add_argument(
        '--sleep',
        dest='sleep',
        help='seconds to wait between broker polling, defaults to service.yaml settings',
        type=int
    )
    args = cmd_args.parse_args()

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s | %(name)s >>> %(message)s',
        datefmt='%d-%b-%Y %H:%M:%S'
    )
    try:
        consume_publish_run(
            CONSUMER,
            DATABASE(args.schema),
            sleep_time=args.sleep if args.sleep else SLEEP_BETWEEN_REQUESTS,
            topics=[args.topic] if args.topic else None,
            cycles=args.cycles if args.cycles else None
        )
    except KeyboardInterrupt:
        sys.exit(0)
