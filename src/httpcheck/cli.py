import asyncio

import click

import httpcheck


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
@click.option("--kafka-ssl-ca")
@click.option("--kafka-ssl-cert")
@click.option("--kafka-ssl-key")
@click.option("--websites")
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
    kafka_ssl_ca,
    kafka_ssl_cert,
    kafka_ssl_key,
):

    monitor_configs = []
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
        monitor_configs.append(monitor_config)

    kafka_config = httpcheck.KafkaConfig(
        broker=kafka_broker,
        topic=kafka_topic,
        ssl_cafile=kafka_ssl_ca,
        ssl_certfile=kafka_ssl_cert,
        ssl_keyfile=kafka_ssl_key,
    )

    # XXX parse websites to add to monitor_configs

    asyncio.run(monitor_all(*monitor_configs, kafka_config=kafka_config))


async def monitor_all(*monitor_configs, kafka_config):
    tasks = []

    for config in monitor_configs:
        coroutine = httpcheck.HttpMonitor(config).monitor_and_publish(kafka_config)
        tasks.append(asyncio.create_task(coroutine))

    for task in tasks:
        await task


if __name__ == "__main__":
    main(auto_envvar_prefix="HTTPCHECK")
