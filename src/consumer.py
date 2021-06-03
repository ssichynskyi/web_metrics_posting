import json
import logging

from typing import Iterable

from kafka import KafkaConsumer


log = logging.getLogger(__name__)

# I've used this example:
# https://github.com/aiven/aiven-examples/blob/master/kafka/python/consumer_example.py
# as well as Aiven Kafka tutorials


class Consumer:

    GROUP_ID = 'web_metrics_consumer'
    CLIENT_ID = 'website-monitoring-consumer-service'

    def __init__(
            self,
            *topics,
            **connection_kwargs
    ):
        """Class for creating Kafka consumer.

        Args:
            *topics - topics to subscribe to. Could be changed during lifetime, str
            **connection_kwargs - keyword arguments as taken by KafkaConsumer
            below there are some useful kwargs and their default value:
                'bootstrap_servers' - uri with port for the service
                'security_protocol' - SSL, SASL_PLAINTEXT, etc
                'sasl_mechanism': None,
                'sasl_plain_username': None,
                'sasl_plain_password': None,
                'ssl_cafile': None,
                'ssl_certfile': None,
                'ssl_keyfile': None
            Note:
                although all params are optional, at least
                'sasl_plain_username' and 'sasl_plain_password'
                or
                'ssl_cafile', 'ssl_certfile' and 'ssl_keyfile
                or other certificate-related inputs shall be defined

        Usage:
            Connection is activated not on object instantiation but
            when entering with statement. e.g.:
            consumer = Consumer(...)
            with consumer:
                consumer.send(...)

        """
        self._topics = topics
        self._connection_data = connection_kwargs
        # auto-determine security protocol if not provided
        try:
            self._connection_data['security_protocol']
        except KeyError:
            username_given = 'sasl_plain_username' in self._connection_data.keys()
            password_given = 'sasl_plain_password' in self._connection_data.keys()
            ca_file_given = 'ssl_cafile' in self._connection_data.keys()
            service_cert_given = 'ssl_certfile' in self._connection_data.keys()
            service_key_given = 'ssl_keyfile' in self._connection_data.keys()
            if all((ca_file_given, service_cert_given, service_key_given)):
                self._connection_data['security_protocol'] = 'SSL'
            elif username_given and password_given:
                self._connection_data['security_protocol'] = 'SASL_PLAINTEXT'
            else:
                msg = 'Security protocol not provided and cannot be determined automatically.'
                msg = f'{msg} Check auth kwargs'
                raise ValueError(msg)
        self._client_id = f'{self.CLIENT_ID}:{id(self)}'

    def __enter__(self):
        """Method which creates the connection. Activated inside with statement."""
        self._consumer = KafkaConsumer(
            *self._topics,
            **self._connection_data,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            client_id=self._client_id,
            group_id=self.GROUP_ID,
            consumer_timeout_ms=1000,
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )
        log.info(f'Connected to kafka broker at: {self._consumer.config["bootstrap_servers"]}')

    def fetch_latest(self):
        """Fetches only not read messages by members of this group.

        Returns:
            list of decoded message values
        """
        self._consumer.poll()
        messages = list()
        for message in self._consumer:
            messages.append(message.value)
        log.info(
            f'Fetched {len(messages)} messages from {self._consumer.config["bootstrap_servers"]}'
        )
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
            # when topics are changed in inactive consumer i.e. not inside `with` statement
            self._topics = topics

    def __exit__(self, exc_type, exc_value, traceback):
        """Actions to perform when exiting with statement."""
        log.info(
            f'Closed connection tp kafka broker at: {self._consumer.config["bootstrap_servers"]}'
        )
