import contextlib
import datetime
import json
import logging

import psycopg2
import pykafka
from pykafka.common import OffsetType


logger = logging.getLogger(__name__)


DDL = [
    """
    CREATE TABLE IF NOT EXISTS attempts (
        id serial NOT NULL PRIMARY KEY,
        url varchar(200) NOT NULL,
        timestamp timestamp with time zone NOT NULL,
        response_time double precision CHECK (response_time > 0),
        is_online boolean NOT NULL,
        status_code smallint CHECK (status_code >= 0),
        identifier varchar(200) NOT NULL,
        exception varchar(200) NOT NULL,
        retries integer NOT NULL CHECK (retries >= 0),
        regex_found boolean NULL,
        UNIQUE (url, identifier, timestamp)
    );
    """,
    "CREATE INDEX IF NOT EXISTS url_idx ON attempts (url);",
    "CREATE INDEX IF NOT EXISTS identifier_idx ON attempts (identifier);",
]


@contextlib.contextmanager
def get_db_cursor(dsn):
    conn = psycopg2.connect(dsn)
    conn.set_session(autocommit=True)
    with conn:
        with conn.cursor() as cur:
            for smt in DDL:
                cur.execute(smt)
            yield cur


def read_from_kafka(kafka_config):
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

    consumer = topic.get_simple_consumer(
        consumer_group="dbimport",
        auto_offset_reset=OffsetType.EARLIEST,
        auto_commit_enable=True,
        reset_offset_on_start=False,
    )

    for message in consumer:
        yield message
        consumer.commit_offsets()


def parse_date(val: str):
    return datetime.datetime.fromisoformat(val)


def import_to_db(database_dsn, kafka_config):
    """ Read from Kafka and write to the database. """
    with get_db_cursor(database_dsn) as cur:
        for msg in read_from_kafka(kafka_config):
            data = json.loads(msg.value)
            try:
                cur.execute(
                    "INSERT INTO attempts (url, timestamp, response_time, is_online, "
                    "status_code, identifier, exception, retries, regex_found) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);",
                    (
                        data["url"],
                        parse_date(data["timestamp"]),
                        data["response_time"],
                        data["is_online"],
                        data["status_code"],
                        data["identifier"] or "",
                        data["exception"] or "",
                        data["retries"],
                        data["regex_found"],
                    ),
                )
            except psycopg2.errors.UniqueViolation:
                logger.exception("Skipping duplicate record")
            print(cur.query)
