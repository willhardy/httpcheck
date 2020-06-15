import pytest

from httpcheck import websitecheck


@pytest.mark.asyncio
async def test_basic(monitor_config, httpx_mock):
    httpx_mock.add_response(url=monitor_config.url)
    output = await websitecheck.run(monitor_config)
    assert output.is_online
    assert output.status_code == 200
    assert output.response_time is not None
    assert output.timestamp is not None
    assert output.url == "http://example.com"
    assert output.exception is None
    assert output.retries == 0
    assert output.regex_found is None
