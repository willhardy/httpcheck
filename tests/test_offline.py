import httpcore
import httpx
import pytest

from httpcheck import websitecheck


@pytest.mark.parametrize("status_code", [400, 404, 500])
@pytest.mark.asyncio
async def test_http_error(monitor_config, httpx_mock, status_code):
    httpx_mock.add_response(url=monitor_config.url, status_code=status_code)
    output = await websitecheck.run(monitor_config)
    assert output.is_online is False
    assert output.exception is None


@pytest.mark.parametrize(
        "exception",
    [
        httpcore.ConnectError("message"),  # DNS problem, SSL certificate error, etc
        httpcore.CloseError("message"),
        httpcore.ReadError("message"),
        httpcore.WriteError("message"),
        httpx.HTTPError("message"),
        httpx.RequestError("message"),
        httpx.TimeoutException("message"),
        httpx.WriteTimeout("message"),
        httpx.PoolTimeout("message"),
        httpx.NetworkError("message"),
        httpx.ReadError("message"),
        httpx.WriteError("message"),
        httpx.ConnectError("message"),
        httpx.CloseError("message"),
        httpx.ProxyError("message"),
        httpx.UnsupportedProtocol("message"),
        httpx.RemoteProtocolError("message"),
        httpx.DecodingError("message"),
        httpx.TooManyRedirects("message"),
    ],
)
@pytest.mark.asyncio
async def test_exception(monitor_config, httpx_mock, exception):
    def raise_exception(*args, **kwargs):
        raise exception

    httpx_mock.add_callback(raise_exception)
    output = await websitecheck.run(monitor_config)
    assert output.is_online is False
    assert output.exception is not None
    assert type(exception).__name__ in output.exception
