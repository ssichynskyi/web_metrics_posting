import json
import logging

from kafka import KafkaConsumer
from typing import Iterable


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

        Usage:
            Connection is activated not on object instantiation but
            when entering with statement. e.g.:
            consumer = Consumer(...)
            with consumer:
                consumer.send(...)

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
        log.info(f'Connected to kafka broker at: {self._service_uri}')

    def fetch_latest(self):
        """Fetches only not read messages by members of this group

        Returns:
            list of decoded message values
        """
        self._consumer.poll()
        messages = list()
        for message in self._consumer:
            messages.append(message.value)
        log.info(f'Fetched {len(messages)} messages from {self._service_uri}')
        self._consumer.commit()
        return messages

    def change_topics(self, topics: Iterable) -> None:
        """Changes Kafka consumer topic statically or dynamically

        Args:
            topics: any iterable: set, list, tuple

        Returns:
            None

        """
        topics = tuple(topics)
        try:
            self._consumer.unsubscribe()
            self._consumer.subscribe(list(topics))
        except AttributeError:
            self._topics = topics

    def __exit__(self, exc_type, exc_value, traceback):
        log.info(f'Closed connection tp kafka broker at: {self._service_uri}')
