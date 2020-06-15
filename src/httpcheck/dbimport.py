import contextlib
import datetime
import json
import logging

import pkg_resources
import psycopg2
import pykafka
from pykafka.common import OffsetType

from .common import KafkaConfig


logger = logging.getLogger(__name__)
DDL_FILENAME = pkg_resources.resource_filename("httpcheck", "sql/ddl.sql")


def main(database_dsn: str, kafka_config: KafkaConfig):
    """ Read from Kafka and write to the database. """
    with get_db_cursor(database_dsn) as cur:
        create_db_schema(cur)
        try:
            for msg in get_messages_from_kafka(kafka_config):
                data = json.loads(msg.value)
                save_data_to_database(cur, data)
        except (KeyboardInterrupt, SystemExit):
            pass


@contextlib.contextmanager
def get_db_cursor(dsn):
    conn = psycopg2.connect(dsn)
    conn.set_session(autocommit=True)
    with conn:
        with conn.cursor() as cur:
            yield cur


def create_db_schema(cur):
    with open(DDL_FILENAME) as f:
        cur.execute(f.read())
    print_last_query(cur)


def get_messages_from_kafka(kafka_config):
    consumer = get_kafka_consumer(kafka_config)
    for message in consumer:
        yield message
        consumer.commit_offsets()


def save_data_to_database(cur, data):
    try:
        cur.execute(
            """INSERT INTO attempts (
                 url,
                 timestamp,
                 response_time,
                 is_online,
                 status_code,
                 hostname,
                 identifier,
                 exception,
                 retries,
                 regex,
                 regex_found
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            (
                data["url"],
                parse_date(data["timestamp"]),
                data["response_time"],
                data["is_online"],
                data["status_code"],
                data["hostname"] or "",
                data["identifier"] or "",
                data["exception"] or "",
                data["retries"],
                data["regex"],
                data["regex_found"],
            ),
        )
        print_last_query(cur)
    except psycopg2.errors.UniqueViolation:
        logger.exception("Skipping duplicate record")


def print_last_query(cur):
    query = " ".join(cur.query.decode("utf8").split())
    logger.info(f"> {query}")
    logger.info(f"< {cur.statusmessage}")


def get_kafka_consumer(kafka_config):
    """ Setup a Kafka connection for the given config and yield messages. """
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

    return topic.get_simple_consumer(
        consumer_group="dbimport",
        auto_offset_reset=OffsetType.EARLIEST,
        auto_commit_enable=True,
        reset_offset_on_start=False,
    )


def parse_date(val: str):
    return datetime.datetime.fromisoformat(val)
