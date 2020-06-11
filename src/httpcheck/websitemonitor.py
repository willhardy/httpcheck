import contextlib
import dataclasses
import datetime
import re
import socket
import timeit
from typing import Optional

import httpcore
import httpx


@dataclasses.dataclass
class WebsiteMonitorConfig:
    url: str
    timeout_connect: int = 5  # seconds
    timeout_read: int = 30  # seconds
    identifier: str = ""
    method: str = "HEAD"
    retries: int = 1
    regex: Optional[str] = None
    frequency_online: int = 300  # seconds
    frequency_offline: int = 60  # seconds


class WebsiteMonitor:
    def __init__(self, config, config_source=None):
        self.config = config
        self.scheduler_job = None
        self.config_source = config_source

    def add_to_scheduler(self, scheduler, publish_fn):
        # Run immediately, scheduler is for future attempts
        scheduler.add_job(self.attempt_and_publish, args=[publish_fn])

        # Schedule repeats
        self.scheduler_job = scheduler.add_job(
            self.attempt_and_publish,
            "interval",
            seconds=self.config.frequency_online,
            args=[publish_fn],
            id=self.config.url,
        )

    def update_scheduler(self, currently_online):
        if self.scheduler_job is not None:
            if currently_online:
                freq = self.config.frequency_online
            else:
                freq = self.config.frequency_offline

            self.scheduler_job.reschedule("interval", seconds=freq)

    def remove_from_scheduler(self):
        if self.scheduler_job is not None:
            self.scheduler_job.remove()

    async def attempt_and_publish(self, publish_fn):
        check = await self.make_attempt()
        self.update_scheduler(check.is_online)
        publish_fn(check)

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
        """ Observer and log the attempt """
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
