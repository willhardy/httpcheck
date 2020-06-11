import contextlib
import dataclasses
import json
import logging

import pykafka
from pykafka.exceptions import LeaderNotAvailable
from pykafka.exceptions import SocketDisconnectedError


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class KafkaConfig:
    broker: str
    topic: str
    ssl_cafile: str
    ssl_certfile: str
    ssl_keyfile: str


def get_publish_fn(kafka_config):
    if kafka_config.broker:
        return get_publish_fn_kafka(kafka_config)
    else:
        return get_publish_fn_text(kafka_config)


def serialize_attempt_log(attempt_log):
    return json.dumps(dataclasses.asdict(attempt_log))


@contextlib.contextmanager
def get_publish_fn_kafka(kafka_config):
    if kafka_config.ssl_keyfile:
        ssl_config = pykafka.connection.SslConfig(
            kafka_config.ssl_cafile,
            certfile=kafka_config.ssl_certfile,
            keyfile=kafka_config.ssl_keyfile,
        )
    else:
        ssl_config = None

    client = pykafka.KafkaClient(hosts=kafka_config.broker, ssl_config=ssl_config)
    topic = client.topics[kafka_config.topic]
    producer = topic.get_producer(required_acks=0)

    def publish_fn(attempt_log):
        nonlocal producer
        data = serialize_attempt_log(attempt_log)
        try:
            producer.produce(data.encode("utf8"))
        except (SocketDisconnectedError, LeaderNotAvailable) as exc:
            logger.warning("Kafka connection lost: %s", exc, exc_info=True)
            producer = topic.get_producer(required_acks=0)
            producer.stop()
            producer.start()
            producer.produce(data.encode("utf8"))

        print(data)

    yield publish_fn

    print("Waiting for remaining messages to be sent...")
    producer.stop()
    print("Done!")


@contextlib.contextmanager
def get_publish_fn_text(logs):
    publish_fn = lambda attempt_log: print(serialize_attempt_log(attempt_log))
    yield publish_fn
