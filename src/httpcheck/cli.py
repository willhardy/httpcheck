import asyncio
import json

import click

import httpcheck


SSLFilePath = click.Path(exists=True, allow_dash=False, dir_ok=False, resolve_path=True)


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
@click.option("--kafka-ssl-cafile", type=SSLFilePath)
@click.option("--kafka-ssl-certfile", type=SSLFilePath)
@click.option("--kafka-ssl-keyfile", type=SSLFilePath)
@click.option("--websites", type=click.File("r"))
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

    if websites:
        websites_data = json.load(websites)
        for key, config in websites_data.items():
            if "url" not in config:
                config["url"] = key
            monitor_configs.append(httpcheck.HttpMonitorConfig(**config))

    kafka_config = httpcheck.KafkaConfig(
        broker=kafka_broker,
        topic=kafka_topic,
        ssl_cafile=kafka_ssl_cafile,
        ssl_certfile=kafka_ssl_certfile,
        ssl_keyfile=kafka_ssl_keyfile,
    )

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
