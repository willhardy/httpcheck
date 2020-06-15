import pytest

from httpcheck.common import WebsiteMonitorConfig


@pytest.fixture
def monitor_config():
    monitor_config = WebsiteMonitorConfig(
        url="http://example.com", retries=0, timeout=0.1,
    )
    return monitor_config
