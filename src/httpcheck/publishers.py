import dataclasses
import logging

import pykafka
from pykafka.exceptions import LeaderNotAvailable
from pykafka.exceptions import SocketDisconnectedError


logger = logging.getLogger(__name__)
REGISTERED_PUBLISHERS = {}


def get_publisher(config):
    backend = config["backend"]
    return REGISTERED_PUBLISHERS[backend](config)


class BasePublisher:
    """ Class that provides a .publish() method that will publish the results.
    """

    key = None

    @dataclasses.dataclass(frozen=True)
    class Config:
        pass

    def __init__(self, config):
        relevant_config_keys = {f.name for f in dataclasses.fields(self.Config)}
        relevant_config = {k: v for k, v in config.items() if k in relevant_config_keys}
        self.config = self.Config(**relevant_config)

    def publish(self, msg):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __init_subclass__(cls, **kwargs):
        REGISTERED_PUBLISHERS[cls.key] = cls
        super().__init_subclass__(**kwargs)


class ConsolePublisher(BasePublisher):
    key = "console"

    def publish(self, data):
        print(data, flush=True)


class KafkaPublisher(BasePublisher):
    key = "kafka"

    @dataclasses.dataclass(frozen=True)
    class Config:
        broker: str
        topic: str
        ssl_cafile: str
        ssl_certfile: str
        ssl_keyfile: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client = self._get_kafka_client()
        self._topic = client.topics[self.config.topic]
        self._producer = self._topic.get_producer(required_acks=0)

    def publish(self, data):
        try:
            self._producer.produce(data.encode("utf8"))
        except (SocketDisconnectedError, LeaderNotAvailable) as exc:
            logger.warning("Kafka connection lost: %s", exc, exc_info=True)
            self._producer = self._topic.get_producer(required_acks=0)
            self._producer.stop()
            self._producer.start()
            self._producer.produce(data.encode("utf8"))

        print(data, flush=True)

    def close(self):
        logger.info("Waiting for all messages to be sent to Kafka...")
        self._producer.stop()
        logger.info("Done!")

    def _get_kafka_client(self):
        if self.config.ssl_keyfile:
            ssl_config = pykafka.connection.SslConfig(
                self.config.ssl_cafile,
                certfile=self.config.ssl_certfile,
                keyfile=self.config.ssl_keyfile,
            )
        else:
            ssl_config = None

        return pykafka.KafkaClient(hosts=self.config.broker, ssl_config=ssl_config)
