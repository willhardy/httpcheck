from unittest import mock

from click.testing import CliRunner

import httpcheck
from httpcheck.cli import main as httpcheck_cli


def test_consistent_defaults(httpx_mock):
    """ Ensure that the default values for CLI are the same as the dataclass itself
    """
    # Create a monitor config with default values for everything
    direct_monitor_config = httpcheck.HttpMonitorConfig("http://example.com")

    # Create a monitor config using the defaults from the CLI
    httpcheck.monitor_all = mock.Mock()
    runner = CliRunner()
    runner.invoke(httpcheck_cli, ["http://example.com"])
    cli_monitor_config = httpcheck.monitor_all.call_args.args[0]["http://example.com"]

    assert cli_monitor_config == direct_monitor_config
