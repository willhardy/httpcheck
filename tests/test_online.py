import pytest


@pytest.mark.asyncio
async def test_basic(monitor, httpx_mock):
    httpx_mock.add_response(monitor.config.url)
    output = await monitor.make_attempt()
    assert output.is_online
    assert output.status_code == 200
    assert output.response_time is not None
    assert output.timestamp is not None
    assert output.url == "http://example.com"
    assert output.method == "GET"
    assert output.exception is None
    assert output.retries == 0
    assert output.regex_found is None
