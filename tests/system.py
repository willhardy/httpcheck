import json
import random
import signal
import string
import subprocess
import sys
import tempfile

import click


def system_test():
    """ Complete end-to-end system test involving most (all?) moving parts.
    """
    # Generate random identifiers to help verify the new data arrived.
    identifier1 = get_random_identifier()
    identifier2 = get_random_identifier()

    # Configure and run httpcheck to monitor two urls;
    #    * one online website defined on command line, every 5s
    #    * one offline website in websites JSON, every 9s
    with tempfile.NamedTemporaryFile("w+") as websites_json:
        url = "http://example.com"
        url_offline = "https://expired.badssl.com/"
        offline_website_conf = {
            url_offline: {"identifier": identifier2, "frequency": 9}
        }
        json.dump(offline_website_conf, websites_json)
        websites_json.flush()

        run(
            f"httpcheck {url} --identifier={identifier1} --frequency=5"
            f" --websites={websites_json.name}",
            timeout=14,
        )

    click.secho("SUCCESS!", fg="green", bold=True)


def assert_equal(actual, expected):
    assert actual == expected, f"{actual} != {expected}"


def get_random_identifier():
    rand = "".join(random.choice(string.ascii_letters) for i in range(10))
    return f"system-test-{rand}"


def run(cmd_str, timeout):
    cmd = cmd_str.split()
    click.secho(f"Running {cmd_str}\n(timeout in {timeout}s...)", fg="yellow")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf8"
    )

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        click.secho("Time over, sending SIGINT", fg="yellow")
        proc.send_signal(signal.SIGINT)
        stdout, stderr = proc.communicate()

    if proc.returncode not in (0,):
        click.secho(f"Call to {cmd_str} failed: exit {proc.returncode}", fg="red")
        click.secho("\nSTDOUT:", fg="red")
        click.secho(stdout)
        click.secho("\nSTDERR:", fg="red")
        click.secho(stderr)
        sys.exit(1)
    else:
        click.secho("\nSTDOUT:", fg="yellow")
        click.secho(stdout)
        click.secho("\nSTDERR:", fg="yellow")
        click.secho(stderr)


if __name__ == "__main__":
    system_test()
