import dataclasses
import json
import logging

import pykafka
from pykafka.exceptions import LeaderNotAvailable
from pykafka.exceptions import SocketDisconnectedError


logger = logging.getLogger(__name__)


def get_publish_fn(kafka_config):
    if kafka_config.broker:
        return get_publish_fn_kafka(kafka_config)
    else:
        return get_publish_fn_text(kafka_config)


def serialize_attempt_log(attempt_log):
    return json.dumps(dataclasses.asdict(attempt_log))


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

    def publish(attempt_log):
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

    return publish


def get_publish_fn_text(logs):
    publish_fn = lambda attempt_log: print(serialize_attempt_log(attempt_log))
    return publish_fn
