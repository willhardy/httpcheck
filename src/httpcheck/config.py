import dataclasses
from typing import Optional


@dataclasses.dataclass
class HttpMonitorConfig:
    url: str
    timeout_connect: int = 5  # seconds
    timeout_read: int = 30  # seconds
    identifier: str = ""
    method: str = "HEAD"
    retries: int = 1
    regex: Optional[str] = None
    frequency_online: int = 300  # seconds
    frequency_offline: int = 60  # seconds


@dataclasses.dataclass
class KafkaConfig:
    broker: str
    topic: str
    ssl_cafile: str
    ssl_certfile: str
    ssl_keyfile: str
