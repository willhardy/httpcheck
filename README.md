# httpcheck

A tool to monitor website availability

## Installation

Install from this directory using pip:

```bash
$ make build
$ pip install build/httpcheck-1.0-py3-none-any.whl
```

Alternatively, we can run it directly in docker:

```bash
$ touch .env
$ docker-compose run --rm httpcheck httpcheck --help
```

## Basic Usage

In its simplest form, `httpcheck` will monitor the URLs provided and output the results to stdout:.

```bash
$ httpcheck https://one.example.com https://two.example.com
{"url": "https://one.example.com", "timestamp": "2020-06-08T17:25:03.141592", ...}
{"url": "https://two.example.com", "timestamp": "2020-06-08T17:25:02.718281", ...}
{"url": "https://two.example.com", "timestamp": "2020-06-08T17:30:02.718281", ...}
{"url": "https://one.example.com", "timestamp": "2020-06-08T17:30:03.141592", ...}
```

Send the `INT` signal (ie type CTRL-C) to stop.


## Output

Each time a website is checked, a simple JSON object is created summarising the attempt.
This is printed to stdout (the entire output will then be [jsonlines](http://jsonlines.org/)).

The JSON object will have the following keys:

 * `url` The URL that was contacted
 * `timestamp` The date/time that the attempt was started (a string in ISO-8601)
 * `identifier` The identifier provided in the configuration and used in the User-Agent header
 * `is_online` This is `true` if the website is contactable and responds with a non-error HTTP status
 * `regex` The regular expression that was configured, if any.
 * `regex_found` This is `true` if the configured regular expression was found. `false` if it was not found, `null` if no regex was configured.
 * `response_time` The time taken to receive the response, in seconds .
 * `status_code` The status code returned by the website.
 * `exception` The type of exception that was raised (if any) while trying to connect.
 * `retries` The number of immediate retries made in this attempt

For example:

```json
{
  "url": "https://example.com",
  "timestamp": "2020-06-08T17:25:23.102321",
  "identifier": "eu-west-1",
  "is_online": true,
  "regex": "example",
  "regex_found": true,
  "response_time": 1.41421356,
  "status_code": 200,
  "exception": null,
  "retries": 0
}
```


## Advanced Usage: `--websites`

To monitor multiple websites with custom configuration, you can use a configuration file.

Here is an example JSON file that can be used to setup two websites to be monitored at different times:

```json
{
  "https://example.com/health1": { "frequency": 300 },
  "https://example.com/health2": { "frequency": 120 }
}
```

The file can be provided using the `--websites` command line option:

```bash
$ httpcheck --websites websites.json
```

If this `websites.json` file changes, you can reload the configuration by sending the `HUP` signal to the process.
The key of the top level object in `websites.json` will be used to update existing tasks and remove any tasks no longer mentioned in the configuration.

If you would like to reserve the ability to seamlessly change the URL, you can use a custom key and provide the URL in the configuration, eg:

```json
{
  "one": {"url": "https://example.com/health1", "frequency": 300 },
  "two": {"url": "https://example.com/health2", "frequency": 120 }
}
```

## Tests

 * Run the full test suite with `make test` (will build and run inside docker).
 * Run a system test by calling `make system-test`

## More information

All command line arguments/environment variables are described in `httpcheck --help`.
Likewise, all available make targets can be listed with `make help`.
