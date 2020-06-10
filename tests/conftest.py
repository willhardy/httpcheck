import pytest

from httpcheck.websitemonitor import WebsiteMonitor
from httpcheck.websitemonitor import WebsiteMonitorConfig


@pytest.fixture
def monitor():
    monitor_config = WebsiteMonitorConfig(
        url="http://example.com", retries=0, timeout_read=0.1, timeout_connect=0.1,
    )
    return WebsiteMonitor(monitor_config)
