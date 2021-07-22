import dataclasses
import datetime
import logging
import socket
from typing import Optional


logger = logging.getLogger(__name__)


def now_isoformat():
    now = datetime.datetime.utcnow().isoformat()
    return f"{now}+00:00"


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


@dataclasses.dataclass
class WebsiteCheckResults:
    """ Run and record the results for a single website check. """

    method: str
    url: str
    timestamp: str = dataclasses.field(default_factory=now_isoformat)
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
        return cls(
            url=config.url,
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
