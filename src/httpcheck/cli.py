import logging
import os

import click

from . import main
from .common import WebsiteMonitorConfig
from .decorators import help_messages


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
        "websites": "Filename for a JSON file multiple website configuration",
        "timezone": "Timezone to report attempts in",
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
@click.option("--websites", type=FilePath)
@click.option("--timezone", default="UTC")
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
    timezone,
    once,
):
    set_log_level_from_environment()

    monitor_configs = {}
    for url in urls:
        monitor_config = WebsiteMonitorConfig(
            identifier=identifier,
            method=method,
            url=url,
            timeout=timeout,
            retries=retries,
            regex=regex,
            frequency=frequency,
            timezone=timezone,
        )
        monitor_configs[url] = monitor_config

    publisher_config = {"backend": "console"}
    main.monitor_all(monitor_configs, publisher_config, websites, once=once)


def set_log_level_from_environment():
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    level = os.environ.get("LOG_LEVEL", "").upper()
    if level in valid_levels:
        logging.basicConfig(level=level)
