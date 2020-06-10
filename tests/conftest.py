import time

import pytest

from httpcheck.config import HttpMonitorConfig
from httpcheck.monitor import HttpMonitor


class TestHttpMonitor(HttpMonitor):
    """ A subclass of our test subject, but with instant sleep """

    def __init__(self, *args, **kwargs):
        self._test_time_offset = 0
        super().__init__(*args, **kwargs)

    def now(self):
        return time.time() + self._test_time_offset

    async def sleep(self, seconds):
        self._test_time_offset += seconds


@pytest.fixture
def monitor():
    monitor_config = HttpMonitorConfig(
        url="http://example.com", retries=0, timeout_read=0.1, timeout_connect=0.1,
    )
    return TestHttpMonitor(monitor_config)
