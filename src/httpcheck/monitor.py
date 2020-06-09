import asyncio
import contextlib
import dataclasses
import datetime
import logging
import re
import time
import timeit
from typing import Optional

import httpcore
import httpx

from . import publish


logger = logging.getLogger(__name__)


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

        self.currently_online = True
        self.time_of_next_attempt = time.time()
        self._asyncio_task = None

    async def make_attempt(self):
        """ Make an attempt to contact the service, returns an AttemptLog. """
        total_attempts = 1 + self.config.retries

        for retry_idx in range(total_attempts):
            logger.debug("Starting attempt: %s", self.config.url)
            attempt_log = AttemptLog(
                retries=retry_idx,
                url=self.config.url,
                identifier=self.config.identifier,
            )
            logger.debug("AttemptLog created: %s", self.config.url)
            try:
                with attempt_log.measure_response_time():
                    logger.debug("Started timer: %s", self.config.url)
                    response = await self.make_http_request()
                    logger.debug("Response completed: %s", self.config.url)
            except (
                httpx.HTTPError,
                httpcore.NetworkError,
                httpcore.TimeoutException,
                httpcore.ProtocolError,
                httpcore.ProxyError,
            ) as exc:
                logger.debug("Exception raised: %s", self.config.url)
                attempt_log.process_exception(exc)
                continue  # Let's maybe retry!
            else:
                logger.debug("No exception raised: %s", self.config.url)
                attempt_log.process_response(response, self.config.regex)
                logger.debug("Response processed: %s", self.config.url)
                break  # No retry necessary, we're done

        self.currently_online = attempt_log.is_online
        logger.debug("Attempt completed: %s", self.config.url)
        return attempt_log

    async def make_http_request(self):
        _timeout = httpx.Timeout(
            connect_timeout=self.config.timeout_connect,
            read_timeout=self.config.timeout_read,
        )
        headers = {"user-agent": f"httpcheck/{self.config.identifier}"}
        async with httpx.AsyncClient(timeout=_timeout, headers=headers) as client:
            logger.debug("HTTP client ready, sending request")
            try:
                return await client.request(self.config.method, self.config.url)
            except Exception:
                logger.exception("Exception raised")
                raise

    async def monitor(self):
        logger.debug("Starting monitor: %s", self.config.url)
        while True:
            yield await self.make_attempt()
            self.schedule_next_attempt()
            await self.sleep_until_next_attempt()

    async def monitor_and_publish(self, kafka_config):
        logs = self.monitor()
        if kafka_config.broker:
            await publish.publish_logs(logs, kafka_config)
        else:
            await publish.publish_logs_text(logs, kafka_config)

    async def get_asyncio_task(self, kafka_config):
        coroutine = self.monitor_and_publish(kafka_config)
        return asyncio.create_task(coroutine)

    @property
    def current_frequency(self):
        if self.currently_online:
            return self.config.frequency_online
        else:
            return self.config.frequency_offline

    def schedule_next_attempt(self):
        time_of_next_attempt = self.time_of_next_attempt + float(self.current_frequency)
        self.time_of_next_attempt = max([time.time(), time_of_next_attempt])

    async def sleep_until_next_attempt(self):
        time_until_next_attempt = max([self.time_of_next_attempt - time.time(), 0])
        await asyncio.sleep(time_until_next_attempt)
