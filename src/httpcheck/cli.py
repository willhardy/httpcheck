import logging
import os

import click

from . import dbimport
from . import main
from .decorators import help_messages
from .websitemonitor import WebsiteMonitorConfig


# Here is a preconfigured click Path type
FilePath = click.Path(exists=True, allow_dash=False, dir_okay=False, resolve_path=True)


def httpcheck_cli():
    httpcheck_main(auto_envvar_prefix="HTTPCHECK")


@help_messages(
    {
        "identifier": "A string for the User-Agent header when making requests",
        "method": "The HTTP method to use",
        "timeout": "Number of seconds to wait for the HTTP response",
        "retries": "Number of immediate retries when HTTP connection fails",
        "regex": "A regular expression to search for in the response",
        "frequency": "Seconds to wait before re-checking website",
        "kafka_broker": "Name and port for the Kafka broker to send results to",
        "kafka_topic": "Name of the topic in Kafka",
        "kafka_ssl_cafile": "Filename for a CA file (Kafka SSL auth)",
        "kafka_ssl_certfile": "Filename for a certificate file (Kafka SSL auth)",
        "kafka_ssl_keyfile": "Filename for a secret (Kafka SSL auth)",
        "websites": "Filename for a JSON file multiple website configuration",
        "once": "Only run the check once for each website, do not monitor",
    }
)
@click.command()
@click.argument("urls", nargs=-1)
@click.option("--identifier", default="")
@click.option("--method", default="HEAD")
@click.option("--timeout", default=30)
@click.option("--retries", default=1)
@click.option("--regex",)
@click.option("--frequency", default=300)
@click.option("--kafka-broker",)
@click.option("--kafka-topic")
@click.option("--kafka-ssl-cafile", type=FilePath)
@click.option("--kafka-ssl-certfile", type=FilePath)
@click.option("--kafka-ssl-keyfile", type=FilePath)
@click.option("--websites", type=FilePath)
@click.option("--once", is_flag=True)
def httpcheck_main(
    urls,
    identifier,
    method,
    timeout,
    retries,
    regex,
    frequency,
    websites,
    kafka_broker,
    kafka_topic,
    kafka_ssl_cafile,
    kafka_ssl_certfile,
    kafka_ssl_keyfile,
    once,
):
    set_log_level_from_environment()

    monitor_configs = {}
    for url in urls:
        monitor_config = WebsiteMonitorConfig(
            identifier=identifier,
            method=method,
            url=url,
            timeout_read=timeout,
            retries=retries,
            regex=regex,
            frequency=frequency,
        )
        monitor_configs[url] = monitor_config

    publisher_config = {
        "backend": "kafka" if kafka_broker else "console",
        "broker": kafka_broker,
        "topic": kafka_topic,
        "ssl_cafile": kafka_ssl_cafile,
        "ssl_certfile": kafka_ssl_certfile,
        "ssl_keyfile": kafka_ssl_keyfile,
    }

    main.monitor_all(monitor_configs, publisher_config, websites, once=once)


def dbimport_cli():
    dbimport_main(auto_envvar_prefix="HTTPCHECK")


@help_messages(
    {
        "database_url": "DSN for connecting to the database",
        "kafka_broker": "Name and port for the Kafka broker to send results to",
        "kafka_topic": "Name of the topic in Kafka",
        "kafka_ssl_cafile": "Filename for a CA file (Kafka SSL auth)",
        "kafka_ssl_certfile": "Filename for a certificate file (Kafka SSL auth)",
        "kafka_ssl_keyfile": "Filename for a secret (Kafka SSL auth)",
    }
)
@click.command()
@click.option("--database-url", envvar="DATABASE_URL", required=True)
@click.option("--kafka-broker", required=True)
@click.option("--kafka-topic", required=True)
@click.option("--kafka-ssl-cafile", type=FilePath)
@click.option("--kafka-ssl-certfile", type=FilePath)
@click.option("--kafka-ssl-keyfile", type=FilePath)
def dbimport_main(
    database_url,
    kafka_broker,
    kafka_topic,
    kafka_ssl_cafile,
    kafka_ssl_certfile,
    kafka_ssl_keyfile,
):
    set_log_level_from_environment()

    kafka_config = dbimport.KafkaConfig(
        broker=kafka_broker,
        topic=kafka_topic,
        ssl_cafile=kafka_ssl_cafile,
        ssl_certfile=kafka_ssl_certfile,
        ssl_keyfile=kafka_ssl_keyfile,
    )
    dbimport.main(database_url, kafka_config)


def set_log_level_from_environment():
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    level = os.environ.get("LOG_LEVEL", "").upper()
    if level in valid_levels:
        logging.basicConfig(level=level)
