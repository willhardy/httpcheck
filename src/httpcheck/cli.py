import click

import httpcheck


# Here is a preconfigured click Path type
FilePath = click.Path(exists=True, allow_dash=False, dir_okay=False, resolve_path=True)


@click.command()
@click.argument("urls", nargs=-1)
@click.option("--identifier", default="")
@click.option("--method", default="HEAD", show_default=True)
@click.option("--timeout", default=30, show_default=True)
@click.option("--retries", default=1, show_default=True)
@click.option("--regex")
@click.option("--frequency-online", default=300, show_default=True)
@click.option("--frequency-offline", default=60, show_default=True)
@click.option("--kafka-broker")
@click.option("--kafka-topic")
@click.option("--kafka-ssl-cafile", type=FilePath)
@click.option("--kafka-ssl-certfile", type=FilePath)
@click.option("--kafka-ssl-keyfile", type=FilePath)
@click.option("--websites", type=FilePath)
@click.option("--once", is_flag=True)
def main(
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
        monitor_config = httpcheck.HttpMonitorConfig(
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

    kafka_config = httpcheck.KafkaConfig(
        broker=kafka_broker,
        topic=kafka_topic,
        ssl_cafile=kafka_ssl_cafile,
        ssl_certfile=kafka_ssl_certfile,
        ssl_keyfile=kafka_ssl_keyfile,
    )

    httpcheck.monitor_all(monitor_configs, kafka_config, websites, once=once)


if __name__ == "__main__":
    main(auto_envvar_prefix="HTTPCHECK")
