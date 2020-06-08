import datetime
import time

import pytest

from httpcheck import HttpMonitor
from httpcheck import HttpMonitorConfig


# This is the epoch for the test suite
# XXX Maybe not needed
FOREVER_NOW = time.mktime(datetime.datetime(2020, 1, 1).timetuple())


class TestHttpMonitor(HttpMonitor):
    """ A subclass of our test subject, but with instant sleep """

    def __init__(self, *args, **kwargs):
        # self._test_time_offset = FOREVER_NOW - time.time()  # XXX maybe not needed
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
