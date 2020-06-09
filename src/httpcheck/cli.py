import click

import httpcheck


FilePath = click.Path(exists=True, allow_dash=False, dir_okay=False, resolve_path=True)


@click.command()
@click.argument("urls", nargs=-1)
@click.option("--identifier", default="")
@click.option("--method", default="GET")
@click.option("--timeout", default=30)
@click.option("--retries", default=2)
@click.option("--regex")
@click.option("--frequency", default=300)
@click.option("--kafka-broker")
@click.option("--kafka-topic")
@click.option("--kafka-ssl-cafile", type=FilePath)
@click.option("--kafka-ssl-certfile", type=FilePath)
@click.option("--kafka-ssl-keyfile", type=FilePath)
@click.option("--websites", type=FilePath)
def main(
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
):

    monitor_configs = {}
    for url in urls:
        monitor_config = httpcheck.HttpMonitorConfig(
            identifier=identifier,
            method=method,
            url=url,
            timeout_read=timeout,
            retries=2,
            regex=regex,
            frequency_online=frequency,
            frequency_offline=frequency,
        )
        monitor_configs[url] = monitor_config

    kafka_config = httpcheck.KafkaConfig(
        broker=kafka_broker,
        topic=kafka_topic,
        ssl_cafile=kafka_ssl_cafile,
        ssl_certfile=kafka_ssl_certfile,
        ssl_keyfile=kafka_ssl_keyfile,
    )

    httpcheck.monitor_all(monitor_configs, kafka_config, websites)


if __name__ == "__main__":
    main(auto_envvar_prefix="HTTPCHECK")
