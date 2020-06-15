import asyncio
import dataclasses
import functools
import json
import signal
import typing

from . import common
from . import publishers
from . import scheduler
from . import websitecheck


def monitor_all(monitor_configs, publisher_config, websites_filename, once=False):
    monitor_configs_from_file = dict(parse_websites_json(websites_filename))
    all_monitor_configs = {**monitor_configs_from_file, **monitor_configs}

    with publishers.get_publisher(publisher_config) as publisher:
        job_fn = functools.partial(check_and_publish, publisher=publisher)
        monitor_manager = MonitorManager(
            monitor_configs=all_monitor_configs, scheduler=scheduler.Scheduler(job_fn),
        )
        if once:
            monitor_manager.run_all_monitors_once()
        else:
            monitor_manager.schedule_all_monitors()


async def check_and_publish(config, publisher):
    check_results = await websitecheck.run(config)
    data = json.dumps(dataclasses.asdict(check_results))
    publisher.publish(data)


@dataclasses.dataclass(frozen=True)
class MonitorManager:
    """ Manage the monitoring of many website, connect them to scheduler.
    """

    monitor_configs: typing.Dict[str, common.WebsiteMonitorConfig]
    scheduler: typing.Optional[any] = None

    def run_all_monitors_once(self):
        common.print_monitor_configs(*self.monitor_configs.values())
        asyncio.run(self.async_run_all_monitors_once())

    async def async_run_all_monitors_once(self):
        coroutines = (
            self.scheduler.run_once(config) for config in self.monitor_configs.values()
        )
        await asyncio.gather(*coroutines)

    def schedule_all_monitors(self):
        common.print_monitor_configs(*self.monitor_configs.values())

        # XXX Where to put results?
        for monitor_config in self.monitor_configs.values():
            self.scheduler.schedule(monitor_config)

        self.scheduler.start()

        signal.signal(signal.SIGHUP, self.reload_config)

        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass

    def reload_config(self, signum, frame):
        """ Reload any changes to the configuration file.

        This provides the ability to reload a changed config file while still
        running, avoiding any extra attempts that might happen on a restart.
        """
        monitor_updates = {}

        filenames = (c.source for c in self.monitor_configs.values() if c.source)
        for filename in filenames:
            monitor_updates.update(parse_websites_json(filename))

        if not monitor_updates:
            return

        for key, monitor_config in self.monitor_configs.items():
            # Leave explicitly configured monitors alone
            if monitor_config.source is None:
                continue

            if key in monitor_updates:
                self.scheduler.reschedule(monitor_config)
            else:
                self.scheduler.unschedule(monitor_config)
                del self.monitor_configs[key]

        new_keys = set(monitor_updates) - set(self.monitor_configs)
        for new_key in new_keys:
            new_config = monitor_updates[new_key]
            self.scheduler.schedule(new_config)
            self.monitor_configs[new_key] = new_config

        common.print_monitor_configs(*self.monitor_configs.values())


def parse_websites_json(filename):
    if not filename:
        return

    with open(filename) as f:
        websites_data = json.load(f)

    for key, config in websites_data.items():
        if "url" not in config:
            config["url"] = key
        config["source"] = filename
        yield key, common.WebsiteMonitorConfig(**config)
