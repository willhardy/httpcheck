import dataclasses
import datetime
import logging
import socket
from typing import Optional

import pytz

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class WebsiteMonitorConfig:
    url: str
    key: Optional[str] = None
    timeout: int = 30  # seconds
    identifier: str = ""
    method: str = "HEAD"
    retries: int = 1
    regex: Optional[str] = None
    frequency: int = 300  # seconds
    source: Optional[str] = None
    timezone: str = "UTC"


@dataclasses.dataclass
class WebsiteCheckResults:
    """ Run and record the results for a single website check. """

    method: str
    url: str
    timestamp: str
    hostname: Optional[str] = dataclasses.field(default_factory=socket.getfqdn)
    identifier: Optional[str] = None
    is_online: Optional[bool] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    regex: Optional[str] = None
    regex_found: Optional[bool] = None
    exception: Optional[Exception] = None
    retries: int = 0

    @classmethod
    def from_config(cls, config):
        timezone = pytz.timezone(config.timezone)
        return cls(
            url=config.url,
            timestamp=datetime.datetime.now(timezone).isoformat(),
            method=config.method,
            identifier=config.identifier,
            regex=config.regex,
        )


def print_monitor_configs(*monitor_configs):
    lines = []
    lines.append("---")
    lines.append("The following websites are configured:")
    for config in monitor_configs:
        lines.append("---")
        for key, val in vars(config).items():
            lines.append(f"{key}: {val}")
    lines.append("---")
    logger.info("\n".join(lines))
