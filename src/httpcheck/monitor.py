import contextlib
import dataclasses
import datetime
import re
import time
import timeit
from typing import Optional

import httpcore
import httpx


def now_isoformat():
    now = datetime.datetime.utcnow().isoformat()
    return f"{now}+00:00"


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

    @contextlib.contextmanager
    def measure_response_time(self):
        start_time = timeit.default_timer()
        yield
        self.response_time = timeit.default_timer() - start_time

    def process_response(self, response, regex):
        self.status_code = response.status_code
        self.is_online = not response.is_error
        if regex:
            self.regex_found = bool(re.search(regex, response.text))

    def process_exception(self, exception):
        if getattr(exception, "response", None):
            self.process_response(exception.response)
        self.is_online = False
        self.exception = type(exception).__name__


class HttpMonitor:
    def __init__(self, config):
        self.config = config

        self.scheduler_job = None
        self.currently_online = True
        self.time_of_next_attempt = time.time()

    async def make_attempt(self):
        """ Make an attempt to contact the service, returns an AttemptLog. """
        total_attempts = 1 + self.config.retries

        for retry_idx in range(total_attempts):
            attempt_log = AttemptLog(
                retries=retry_idx,
                url=self.config.url,
                identifier=self.config.identifier,
            )
            try:
                with attempt_log.measure_response_time():
                    response = await self.make_http_request()
            except (
                httpx.HTTPError,
                httpcore.NetworkError,
                httpcore.TimeoutException,
                httpcore.ProtocolError,
                httpcore.ProxyError,
            ) as exc:
                attempt_log.process_exception(exc)
                continue  # Let's maybe retry!
            else:
                attempt_log.process_response(response, self.config.regex)
                break  # No retry necessary, we're done

        self.set_currently_online(attempt_log.is_online)
        return attempt_log

    async def make_http_request(self):
        _timeout = httpx.Timeout(
            connect_timeout=self.config.timeout_connect,
            read_timeout=self.config.timeout_read,
        )
        headers = {"user-agent": f"httpcheck/{self.config.identifier}"}
        async with httpx.AsyncClient(timeout=_timeout, headers=headers) as client:
            return await client.request(self.config.method, self.config.url)

    def update_scheduler(self):
        if self.scheduler_job is None:
            return
        self.scheduler_job.reschedule("interval", seconds=self.current_frequency)

    def remove_from_scheduler(self):
        if self.scheduler_job is None:
            return
        self.scheduler_job.remove()

    def add_to_scheduler(self, scheduler, publish_fn):
        # Run immediately and schedule repeats
        scheduler.add_job(self.attempt_and_publish, args=[publish_fn])
        self.scheduler_job = scheduler.add_job(
            self.attempt_and_publish,
            "interval",
            seconds=self.current_frequency,
            args=[publish_fn],
            id=self.config.url,
        )

    def set_currently_online(self, value):
        self.currently_online = value
        self.update_scheduler()

    async def attempt_and_publish(self, publish_fn):
        log = await self.make_attempt()
        publish_fn(log)

    @property
    def current_frequency(self):
        if self.currently_online:
            return self.config.frequency_online
        else:
            return self.config.frequency_offline
