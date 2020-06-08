import datetime

import httpcore
import pytest
import pytest_httpx


@pytest.mark.asyncio
async def test_custom_method(monitor, httpx_mock):
    monitor.config.method = "PUT"
    httpx_mock.add_response(url=monitor.config.url, method="PUT")
    output = await monitor.make_attempt()
    assert output.is_online is True


@pytest.mark.asyncio
async def test_regex(monitor, httpx_mock):
    monitor.config.regex = r"testtest"
    httpx_mock.add_response(url=monitor.config.url, data="testtest")
    output = await monitor.make_attempt()
    assert output.regex_found is True

    httpx_mock.add_response(url=monitor.config.url, data="test no test")
    output = await monitor.make_attempt()
    assert output.regex_found is False


@pytest.mark.asyncio
async def test_retries(monitor, httpx_mock):
    monitor.config.retries = 2
    times_called = 0

    def raise_exception_once(*args, **kwargs):
        nonlocal times_called
        times_called += 1
        if times_called == 1:
            raise httpcore.ConnectError()
        return pytest_httpx.to_response()

    httpx_mock.add_callback(raise_exception_once)

    output = await monitor.make_attempt()
    assert output.retries == 1
    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.asyncio
async def test_identifier(monitor, httpx_mock):
    monitor.config.identifier = "hello"
    httpx_mock.add_response()
    await monitor.make_attempt()
    (request1,) = httpx_mock.get_requests()
    assert request1.headers["user-agent"] == "httpcheck/hello"


@pytest.mark.skip("timeout?")
@pytest.mark.asyncio
async def test_frequency(monitor, httpx_mock):
    # Alternatve online and offline
    status_codes = [200, 500, 200, 500, 500]

    def alternating_status_code(*args, **kwargs):
        sc = status_codes.pop(0) if status_codes else 200
        return pytest_httpx.to_response(status_code=sc)

    httpx_mock.add_callback(alternating_status_code)

    monitor.frequency_online = 20
    monitor.frequency_offline = 3
    logs = monitor.monitor()
    get_dt = lambda val: datetime.datetime.fromisoformat(val.timestamp)

    # Create a list of the seconds between each attempt
    deltas = []

    # async generator means old school looping
    t0 = get_dt(await logs.__anext__())
    i = 0
    async for log in logs:
        if i >= 5:
            break
        ti = get_dt(log)
        deltas.append(int((ti - t0).total_seconds()))
        t0 = ti
        i += 1

    assert deltas == [20, 3, 20, 3, 3]
