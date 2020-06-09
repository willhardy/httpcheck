import dataclasses
import json

import pykafka


def get_publish_fn(kafka_config):
    if kafka_config.broker:
        return get_publish_fn_kafka(kafka_config)
    else:
        return get_publish_fn_text(kafka_config)


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
    producer = topic.get_producer()

    def publish(attempt_log):
        data = json.dumps(dataclasses.asdict(attempt_log))
        print(data)
        producer.produce(data.encode("utf8"))

    return publish


def get_publish_fn_text(logs):
    publish_fn = lambda log: print(json.dumps(dataclasses.asdict(log)))
    return publish_fn
