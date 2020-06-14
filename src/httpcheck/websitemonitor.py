import contextlib
import dataclasses
import datetime
import json
import re
import socket
import timeit
from typing import Optional

import httpcore
import httpx


@dataclasses.dataclass
class WebsiteMonitorConfig:
    url: str
    key: Optional[str] = None
    timeout_connect: int = 5  # seconds
    timeout_read: int = 30  # seconds
    identifier: str = ""
    method: str = "HEAD"
    retries: int = 1
    regex: Optional[str] = None
    frequency: int = 300  # seconds


class WebsiteMonitor:
    def __init__(self, config, config_source=None):
        self.config = config
        self.config_source = config_source

    @property
    def key(self):
        return self.config.key or self.config.url

    @property
    def frequency(self):
        return self.config.frequency

    async def attempt_and_publish(self, publisher):
        check = await self.make_attempt()
        data = json.dumps(dataclasses.asdict(check))
        publisher.publish(data)

    async def make_attempt(self):
        check = WebsiteCheck(
            url=self.config.url,
            identifier=self.config.identifier,
            regex=self.config.regex,
        )
        await check.run(self.make_http_request, self.config.retries)
        return check

    async def make_http_request(self):
        _timeout = httpx.Timeout(
            connect_timeout=self.config.timeout_connect,
            read_timeout=self.config.timeout_read,
        )
        headers = {"user-agent": f"httpcheck/{self.config.identifier}"}
        async with httpx.AsyncClient(timeout=_timeout, headers=headers) as client:
            return await client.request(self.config.method, self.config.url)


def now_isoformat():
    now = datetime.datetime.utcnow().isoformat()
    return f"{now}+00:00"


@dataclasses.dataclass
class WebsiteCheck:
    """ Run and record the results for a single website check. """

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

    @contextlib.contextmanager
    def measure_response_time(self):
        start_time = timeit.default_timer()
        yield
        self.response_time = timeit.default_timer() - start_time

    def process_response(self, response, regex):
        """ Given a completed response, extract the relevant data. """
        self.status_code = response.status_code
        self.is_online = not response.is_error
        if regex:
            self.regex = regex
            self.regex_found = bool(re.search(regex, response.text))

    def process_exception(self, exception):
        """ Given a exception from an HTTP request, extract the relevant data. """
        if getattr(exception, "response", None):
            self.process_response(exception.response)
        self.is_online = False
        self.exception = type(exception).__name__

    async def run(self, get_response, retries):
        """ Make the attempt and log the results """
        total_attempts = 1 + retries

        for retry_idx in range(total_attempts):
            self.retries = retry_idx

            try:
                with self.measure_response_time():
                    response = await get_response()
            except (
                httpx.HTTPError,
                httpcore.NetworkError,
                httpcore.TimeoutException,
                httpcore.ProtocolError,
                httpcore.ProxyError,
            ) as exc:
                self.process_exception(exc)
                continue  # Let's maybe retry!
            else:
                self.process_response(response, self.regex)
                break  # No retry necessary, we're done
