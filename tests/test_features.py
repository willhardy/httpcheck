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
