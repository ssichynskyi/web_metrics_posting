import argparse
import logging
import os
import time


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


SLEEP_BETWEEN_REQUESTS = config['Metrics endpoint']['Aiven']['upload every']
_kafka_url = config['Metrics endpoint']['Aiven']['Kafka']['host']
_kafka_port = str(config['Metrics endpoint']['Aiven']['Kafka']['port'])
_kafka_uri = ':'.join((_kafka_url, _kafka_port))
_ca_path = os.environ['CA-CERT']
_cert_path = os.environ['SERVICE-CERT']
_key_path = os.environ['SERVICE-KEY']

AIVEN_KAFKA_CONSUMER = Consumer(
    TOPIC,
    service_uri=_kafka_uri,
    ca_path=_ca_path,
    cert_path=_cert_path,
    key_path=_key_path
)

DATABASE = WebMonitoringDBWrapper(
    'website_metrics',
    os.environ['DB_LOGIN'],
    os.environ['DB_PASS'],
    config['Metrics endpoint']['Aiven']['Postgres']['host'],
    config['Metrics endpoint']['Aiven']['Postgres']['port']
)


def consume_publish_run(
        consumer: Consumer,
        db_wrapper: WebMonitoringDBWrapper,
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
    with consumer:
        counter = 0
        def proceed(): return counter < cycles if cycles else True
        while True:
            data = consumer.fetch_latest()
            if not data:
                log.warning('No data to push to DB. Is web metric service running?')
            else:
                db_wrapper.insert(data)
            counter += 1
            if not proceed():
                break
            time.sleep(sleep_time)


if __name__ == '__main__':
    cmd_args = argparse.ArgumentParser()

    cmd_args.add_argument(
        '--topic',
        dest='topic',
        help=f'topic name to publish, no quotes. Defaults to {TOPIC}',
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
    consume_publish_run(
        AIVEN_KAFKA_CONSUMER,
        DATABASE,
        sleep_time=args.sleep if args.sleep else SLEEP_BETWEEN_REQUESTS,
        topics=[args.topic] if args.topic else None,
        cycles=args.cycles if args.cycles else None
    )
