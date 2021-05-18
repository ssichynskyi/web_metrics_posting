import logging
import os
import time

from src.postgres_wrapper import WebMonitoringDBWrapper
from src.consumer import Consumer
from utils.env_config import config


def main(consumer: Consumer, db_wrapper: WebMonitoringDBWrapper, sleep_time: int):
    """Service runner for fetching data from Kafka broker and posting to DB

    Args:
        consumer: Kafka consumer
        db_wrapper: helper lib to work with DB
        sleep_time: number of seconds to wait between metric collection

    Returns:
        None, runs until interrupted by user

    """
    log = logging.getLogger('ConsumerAndSharingService')
    with consumer:
        while True:
            data = consumer.fetch_latest()
            if not data:
                log.warning('No data to push to DB. Is web metric service running?')
            else:
                db_wrapper.insert(data)
            time.sleep(sleep_time)


if __name__ == '__main__':
    sleep_after_request = config['Metrics endpoint']['Aiven']['upload every']
    _kafka_url = config['Metrics endpoint']['Aiven']['Kafka']['host']
    _kafka_port = str(config['Metrics endpoint']['Aiven']['Kafka']['port'])
    kafka_uri = ':'.join((_kafka_url, _kafka_port))
    ca_path = os.environ['CA-CERT']
    cert_path = os.environ['SERVICE_CERT']
    key_path = os.environ['SERVICE-KEY']
    # ToDo: pass topic as a sys arg
    aiven_kafka_consumer = Consumer(
        'website-metrics',
        service_uri=kafka_uri,
        ca_path=ca_path,
        cert_path=cert_path,
        key_path=key_path
    )
    db = WebMonitoringDBWrapper(
        'website_metrics',
        os.environ['DB_LOGIN'],
        os.environ['DB_PASS'],
        config['Metrics endpoint']['Aiven']['Postgres']['host'],
        config['Metrics endpoint']['Aiven']['Postgres']['port']
    )
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s | %(name)s >>> %(message)s',
        datefmt='%d-%b-%Y %H:%M:%S'
    )
    main(aiven_kafka_consumer, db, sleep_after_request)
