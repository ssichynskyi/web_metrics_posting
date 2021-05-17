import json
import logging
import os

from kafka import KafkaConsumer
from utils.env_config import config


log = logging.getLogger(__name__)

# I've used this example:
# https://github.com/aiven/aiven-examples/blob/master/kafka/python/consumer_example.py
# as well as Aiven Kafka tutorials


class Consumer:

    GROUP_ID = 'web_metrics_consumer'
    CLIENT_ID = 'website-monitoring-consumer-service'

    def __init__(self, *topics, service_uri: str, ca_path: str, cert_path: str, key_path: str):
        """Class for creating Kafka consumer

        Args:
            service_uri: uri to active Kafka broker service
            ca_path: path to CA certificate
            cert_path: service cert path
            key_path: service cert key path

        """
        self._topics = topics
        self._service_uri = service_uri
        self._ca_path = ca_path
        self._cert_path = cert_path
        self._key_path = key_path
        self._client_id = f'{self.CLIENT_ID}:{id(self)}'

    def __enter__(self):
        self._consumer = KafkaConsumer(
            *self._topics,
            bootstrap_servers=self._service_uri,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            client_id=self._client_id,
            group_id=self.GROUP_ID,
            security_protocol="SSL",
            ssl_cafile=self._ca_path,
            ssl_certfile=self._cert_path,
            ssl_keyfile=self._key_path,
            consumer_timeout_ms=1000,
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )

    def fetch_latest(self):
        """Fetches only not read messages by members of this group

        Returns:
            list of decoded message values
        """
        self._consumer.poll()
        messages = list()
        for message in self._consumer:
            messages.append(message.value)
        self._consumer.commit()
        return messages

    def __exit__(self, exc_type, exc_value, traceback):
        self._consumer.close(autocommit=True)


_kafka_url = config['Metrics endpoint']['Aiven']['Kafka']['host']
_kafka_port = str(config['Metrics endpoint']['Aiven']['Kafka']['port'])
kafka_uri = ':'.join((_kafka_url, _kafka_port))
ca_path = os.environ['CA-CERT']
cert_path = os.environ['SERVICE_CERT']
key_path = os.environ['SERVICE-KEY']

aiven_kafka_consumer = Consumer('website-metrics', service_uri=kafka_uri, ca_path=ca_path, cert_path=cert_path, key_path=key_path)
with aiven_kafka_consumer:
    a = aiven_kafka_consumer.fetch_latest()

print(a)
