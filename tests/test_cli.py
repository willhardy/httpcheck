from unittest import mock

from click.testing import CliRunner

from httpcheck import main
from httpcheck.cli import httpcheck_main as httpcheck_cli
from httpcheck.common import WebsiteMonitorConfig


def test_consistent_defaults(httpx_mock):
    """ Ensure that the default values for CLI are the same as the dataclass itself
    """
    # Create a monitor config with default values for everything
    direct_monitor_config = WebsiteMonitorConfig("http://example.com")

    # Create a monitor config using the defaults from the CLI
    main.monitor_all = mock.Mock()
    runner = CliRunner()
    runner.invoke(httpcheck_cli, ["http://example.com"])

    assert main.monitor_all.called
    cli_monitor_config = main.monitor_all.call_args.args[0]["http://example.com"]

    assert cli_monitor_config == direct_monitor_config
