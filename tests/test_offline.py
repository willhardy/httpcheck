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
    "exception_class",
    [
        httpcore.ConnectError,  # DNS problem, SSL certificate error, etc
        httpcore.CloseError,
        httpcore.ReadError,
        httpcore.WriteError,
        httpx.ConnectTimeout,
        httpx.CookieConflict,
        httpx.DecodingError,
        httpx.HTTPError,
        httpx.InvalidURL,
        httpx.NetworkError,
        httpx.NotRedirectResponse,
        httpx.PoolTimeout,
        httpx.ProtocolError,
        httpx.ProxyError,
        httpx.ReadTimeout,
        httpx.RequestBodyUnavailable,
        httpx.RequestNotRead,
        httpx.ResponseClosed,
        httpx.ResponseNotRead,
        httpx.StreamConsumed,
        httpx.TooManyRedirects,
        httpx.WriteTimeout,
    ],
)
@pytest.mark.asyncio
async def test_exception(monitor_config, httpx_mock, exception_class):
    def raise_exception(*args, **kwargs):
        raise exception_class()

    httpx_mock.add_callback(raise_exception)
    output = await websitecheck.run(monitor_config)
    assert output.is_online is False
    assert output.exception is not None
    assert exception_class.__name__ in output.exception
