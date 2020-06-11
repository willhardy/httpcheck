import click

from . import dbimport
from . import main
from .publish import KafkaConfig
from .websitemonitor import WebsiteMonitorConfig


# Here is a preconfigured click Path type
FilePath = click.Path(exists=True, allow_dash=False, dir_okay=False, resolve_path=True)


def httpcheck_cli():
    httpcheck_main(auto_envvar_prefix="HTTPCHECK")


@click.command()
@click.argument("urls", nargs=-1)
@click.option(
    "--identifier",
    default="",
    help="A string to be used in the User-Agent header when making requests.",
)
@click.option(
    "--method", default="HEAD", show_default=True, help="The HTTP method to use"
)
@click.option(
    "--timeout",
    default=30,
    show_default=True,
    help="Number of seconds to wait for the response after an HTTP connection is made",
)
@click.option(
    "--retries",
    default=1,
    show_default=True,
    help="Number of immediate retries to make if a connection error occurs",
)
@click.option("--regex", help="A regular expression to search for in the response")
@click.option(
    "--frequency-online",
    default=300,
    show_default=True,
    help="Number of seconds to wait before checking an online website again",
)
@click.option(
    "--frequency-offline",
    default=60,
    show_default=True,
    help="Number of seconds to wait before checking an offline website again",
)
@click.option(
    "--kafka-broker", help="Name and port for the Kafka broker to send results to."
)
@click.option("--kafka-topic", help="Name of the topic in Kafka")
@click.option(
    "--kafka-ssl-cafile",
    type=FilePath,
    help="A filename for a CA file for connecting to Kafka via SSL",
)
@click.option(
    "--kafka-ssl-certfile",
    type=FilePath,
    help="A filename for a certificate file for connecting to Kafka via SSL",
)
@click.option(
    "--kafka-ssl-keyfile",
    type=FilePath,
    help="A filename for a secret keyfile for connecting to Kafka via SSL",
)
@click.option(
    "--websites",
    type=FilePath,
    help="A filename for a configuration file with many websites and custom configuration",
)
@click.option("--once", is_flag=True, help="Only run each check once and exit")
def httpcheck_main(
    urls,
    identifier,
    method,
    timeout,
    retries,
    regex,
    frequency_online,
    frequency_offline,
    websites,
    kafka_broker,
    kafka_topic,
    kafka_ssl_cafile,
    kafka_ssl_certfile,
    kafka_ssl_keyfile,
    once,
):

    monitor_configs = {}
    for url in urls:
        monitor_config = WebsiteMonitorConfig(
            identifier=identifier,
            method=method,
            url=url,
            timeout_read=timeout,
            retries=retries,
            regex=regex,
            frequency_online=frequency_online,
            frequency_offline=frequency_offline,
        )
        monitor_configs[url] = monitor_config

    kafka_config = KafkaConfig(
        broker=kafka_broker,
        topic=kafka_topic,
        ssl_cafile=kafka_ssl_cafile,
        ssl_certfile=kafka_ssl_certfile,
        ssl_keyfile=kafka_ssl_keyfile,
    )

    main.monitor_all(monitor_configs, kafka_config, websites, once=once)


def dbimport_cli():
    dbimport_main(auto_envvar_prefix="HTTPCHECK")


@click.command()
@click.option(
    "--database-url",
    help="DSN for connecting to the database",
    envvar="DATABASE_URL",
    required=True,
)
@click.option(
    "--kafka-broker",
    help="Name and port for the Kafka broker to send results to.",
    required=True,
)
@click.option("--kafka-topic", help="Name of the topic in Kafka", required=True)
@click.option(
    "--kafka-ssl-cafile",
    type=FilePath,
    help="A filename for a CA file for connecting to Kafka via SSL",
)
@click.option(
    "--kafka-ssl-certfile",
    type=FilePath,
    help="A filename for a certificate file for connecting to Kafka via SSL",
)
@click.option(
    "--kafka-ssl-keyfile",
    type=FilePath,
    help="A filename for a secret keyfile for connecting to Kafka via SSL",
)
def dbimport_main(
    database_url,
    kafka_broker,
    kafka_topic,
    kafka_ssl_cafile,
    kafka_ssl_certfile,
    kafka_ssl_keyfile,
):
    kafka_config = KafkaConfig(
        broker=kafka_broker,
        topic=kafka_topic,
        ssl_cafile=kafka_ssl_cafile,
        ssl_certfile=kafka_ssl_certfile,
        ssl_keyfile=kafka_ssl_keyfile,
    )
    dbimport.main(database_url, kafka_config)
