import dataclasses
import json

import pykafka


async def publish_logs(logs, kafka_config):
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
    async for attempt_log in logs:
        data = json.dumps(dataclasses.asdict(attempt_log))
        print(data)
        producer.produce(data.encode("utf8"))


async def publish_logs_text(logs, kafka_config):
    async for attempt_log in logs:
        data = json.dumps(dataclasses.asdict(attempt_log))
        print(data)
