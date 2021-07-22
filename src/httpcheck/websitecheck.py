import contextlib
import re
import timeit

import httpcore
import httpx

from .common import WebsiteCheckResults
from .common import WebsiteMonitorConfig


async def run(config: WebsiteMonitorConfig):
    """ Make the attempt and collate the results """
    results = WebsiteCheckResults.from_config(config)

    total_attempts = 1 + config.retries
    for retry_idx in range(total_attempts):
        results.retries = retry_idx
        try:
            with _measure_response_time(results):
                response = await make_http_request(config)
        except ConnectionError as exc:
            _process_exception(exc, results)
            continue  # Let's maybe retry!
        else:
            _process_response(response, results)
            break  # No retry necessary, we're done

    return results


@contextlib.contextmanager
def _measure_response_time(results):
    start_time = timeit.default_timer()
    yield
    results.response_time = timeit.default_timer() - start_time


def _process_response(response, results):
    """ Given a completed response, extract the relevant data. """
    results.status_code = response.status_code
    results.is_online = not response.is_error
    if results.regex:
        results.regex_found = bool(re.search(results.regex, response.text))


def _process_exception(exception, results):
    """ Given a exception from an HTTP request, extract the relevant data. """
    if getattr(exception, "response", None):
        _process_response(exception.response, results)
    results.is_online = False
    results.exception = " ".join(exception.args)


async def make_http_request(config):
    _timeout = httpx.Timeout(5, read=config.timeout)
    headers = {"user-agent": f"httpcheck/{config.identifier}"}
    async with httpx.AsyncClient(timeout=_timeout, headers=headers) as client:
        try:
            return await client.request(config.method, config.url)
        except (
            httpx.HTTPError,
            httpcore.NetworkError,
            httpcore.TimeoutException,
            httpcore.ProtocolError,
            httpcore.ProxyError,
        ) as exc:
            msg = type(exc).__name__
            raise ConnectionError(msg) from exc
