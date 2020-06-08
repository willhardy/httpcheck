import asyncio
import dataclasses
import datetime
import time
from typing import Optional


def now_isoformat():
    return datetime.datetime.utcnow().isoformat()


@dataclasses.dataclass
class AttemptLog:
    """ This is the recorded result of an attempted request """

    url: str
    timestamp: str = dataclasses.field(default_factory=now_isoformat)
    identifier: Optional[str] = None
    is_online: Optional[bool] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    regex_found: Optional[bool] = None
    exception: Optional[Exception] = None
    retries: int = 0


class HttpMonitor:
    def __init__(self, config):
        self.config = config

    async def make_attempt(self):
        """ Make an attempt to contact the service, returns an AttemptLog. """
        return AttemptLog(self.config.url)

    async def monitor(self):
        while True:
            yield await self.make_attempt()

    def now(self):
        return time.time()

    async def sleep(self, seconds):
        await asyncio.sleep(seconds)
