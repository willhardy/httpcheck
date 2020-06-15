import httpcore
import pytest
import pytest_httpx

from httpcheck import websitecheck


def new_config(old_config, **updates):
    kwargs = {**vars(old_config), **updates}
    Config = type(old_config)
    return Config(**kwargs)


@pytest.mark.asyncio
async def test_custom_method(monitor_config, httpx_mock):
    monitor_config = new_config(monitor_config, method="PUT")
    httpx_mock.add_response(url=monitor_config.url, method="PUT")
    output = await websitecheck.run(monitor_config)
    assert output.is_online is True


@pytest.mark.asyncio
async def test_regex(monitor_config, httpx_mock):
    monitor_config = new_config(monitor_config, regex=r"testtest")
    httpx_mock.add_response(url=monitor_config.url, data="testtest")
    output = await websitecheck.run(monitor_config)
    assert output.regex_found is True

    httpx_mock.add_response(url=monitor_config.url, data="test no test")
    output = await websitecheck.run(monitor_config)
    assert output.regex_found is False


@pytest.mark.asyncio
async def test_retries(monitor_config, httpx_mock):
    monitor_config = new_config(monitor_config, retries=2)
    times_called = 0

    def raise_exception_once(*args, **kwargs):
        nonlocal times_called
        times_called += 1
        if times_called == 1:
            raise httpcore.ConnectError()
        return pytest_httpx.to_response()

    httpx_mock.add_callback(raise_exception_once)

    output = await websitecheck.run(monitor_config)
    assert output.retries == 1
    assert len(httpx_mock.get_requests()) == 2


@pytest.mark.asyncio
async def test_identifier(monitor_config, httpx_mock):
    monitor_config = new_config(monitor_config, identifier="hello")
    httpx_mock.add_response()
    await websitecheck.run(monitor_config)
    (request1,) = httpx_mock.get_requests()
    assert request1.headers["user-agent"] == "httpcheck/hello"
