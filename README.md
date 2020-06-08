# httpcheck

A tool to monitor website availability

## Basic Usage

Run the following command to monitor the URL https://example.com using the default settings:

```bash
$ httpcheck https://example.com
{"url": "https://example.com", "timestamp": "2020-06-08T17:25:03.141592", ...}
{"url": "https://example.com", "timestamp": "2020-06-08T17:30:02.718281", ...}
```

Send the `INT` signal (ie type CTRL-C) to stop.

You can provide multiple URLs a number of options to change the behaviour for all monitored websites at once:
```bash
$ httpcheck https://one.example.com https://two.example.com --frequency 60
{"url": "https://one.example.com", "timestamp": "2020-06-08T17:25:03.141592", ...}
{"url": "https://two.example.com", "timestamp": "2020-06-08T17:25:02.718281", ...}
{"url": "https://two.example.com", "timestamp": "2020-06-08T17:30:02.718281", ...}
{"url": "https://one.example.com", "timestamp": "2020-06-08T17:30:03.141592", ...}
```

Note that the order of output is not guaranteed to be sorted, but will roughly be ordered by `timestamp` + `response_time`.

## Command line options

The following parameters are available, each takes a single argument:

* `--method` The HTTP method to use (default: `GET`)
* `--identifier` A string to be used in the User-Agent header when making requests.
* `--timeout` Number of seconds to wait for the response after an HTTP connection is made (default: `30`)
* `--retries` Number of immediate retries to make if a connection error occurs (default: `1`)
* `--regex` A regular expression to search for in the response
* `--frequency-online` Number of seconds to wait before checking an online website again (default: `300`)
* `--frequency-offline` Number of seconds to wait before checking an offline website again (default: `60`)
* `--frequency` Number of seconds, sets both online and offline frequency to this value
* `--kafka-broker` Name and port for the Kafka broker to send results to.
* `--kafka-topic` Name of the topic in Kafka
* `--kafka-ssl-cafile` A filename for a CA file for connecting to Kafka via SSL
* `--kafka-ssl-certfile` A filename for a certificate file for connecting to Kafka via SSL
* `--kafka-ssl-keyfile` A filename for a secret keyfile for connecting to Kafka via SSL
* `--websites` A filename for a configuration file with many websites and custom configuration (see below)

All of these options can be provided by environment variables, eg `HTTPCHECK_FREQUENCY_ONLINE=30`.


## Output

Each time a website is checked, a simple JSON object is created summarising the attempt.
This is printed to stdout (the entire output will then be [jsonlines](http://jsonlines.org/)).
The output can also be optionally sent to the configured Kafka instance.

The JSON object will have the following keys:

 * `url` The URL that was contacted
 * `timestamp` The date/time that the attempt was started (a string in ISO-8601)
 * `identifier` The identifier provided in the configuration and used in the User-Agent header
 * `is_online` This is `true` if the website is contactable and responds with a non-error HTTP status
 * `regex_found` This is `true` if the configured regular expression was found. `false` if it was not found, `null` if no regex was configured.
 * `response_time` The time taken to receive the response, in seconds .
 * `status_code` The status code returned by the website.
 * `exception` The type of exception that was raised (if any) while trying to connect.
 * `retries` The number of immediate retries made in this attempt

For example:

```json
{
  "url": "https://example.com,
  "timestamp": "2020-06-08T17:25:23.102321",
  "identifier": "eu-west-1",
  "is_online": true,
  "regex_found": true,
  "response_time": 1.41421356,
  "status_code": 200,
  "exception": null,
  "retries": 0,
}
```


## Advanced Usage: `--websites`

To monitor multiple websites with custom configuration, you can use a configuration file.

Here is an example JSON file that can be used to setup two websites to be monitored at different times:

```json
{
  "https://example.com/health1": { "frequency_online": 300  },
  "https://example.com/health2": { "frequency_online": 120, "frequency_offline": 30 }
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
  "one": {"url": "https://example.com/health1", "frequency_online": 300  },
  "two": {"url": "https://example.com/health2", "frequency_online": 120, "frequency_offline": 30 }
}
```

Note that the Kafka configuration cannot be overriden on a per-website basis, it must be provided on the command line or in environment variables.
