import asyncio
import dataclasses
import json
import signal
from typing import Dict
from typing import Optional

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler

from . import publishers
from .websitemonitor import WebsiteMonitor
from .websitemonitor import WebsiteMonitorConfig


def monitor_all(monitor_configs, publisher_config, websites_filename, once=False):
    monitors = {key: WebsiteMonitor(config) for key, config in monitor_configs.items()}
    monitors.update(parse_websites_json(websites_filename))
    with publishers.get_publisher(publisher_config) as publisher:
        monitor_manager = MonitorManager(monitors=monitors, publisher=publisher)
        if once:
            monitor_manager.run_all_monitors_once()
        else:
            monitor_manager.schedule_all_monitors()


@dataclasses.dataclass
class SchedulerFacade:
    scheduler: BaseScheduler
    publisher: publishers.BasePublisher

    def start(self):
        self.scheduler.start()

    def get_job_id(self, website_monitor):
        return f"httpcheck:{website_monitor.key}"

    def schedule(self, website_monitor):
        job_id = self.get_job_id(website_monitor)

        # Run immediately, AsyncScheduler does not start with an immediate job
        self.scheduler.add_job(
            website_monitor.attempt_and_publish, args=[self.publisher]
        )

        # Schedule repeats
        self.scheduler.add_job(
            website_monitor.attempt_and_publish,
            trigger="interval",
            seconds=website_monitor.frequency,
            args=[self.publisher],
            id=job_id,
            replace_existing=True,
        )

    def reschedule(self, website_monitor):
        job_id = self.get_job_id(website_monitor)
        try:
            self.scheduler.reschedule_job(
                job_id, trigger="interval", seconds=website_monitor.frequency
            )
        except JobLookupError:
            self.schedule(website_monitor)

    def unschedule(self, website_monitor):
        job_id = self.get_job_id(website_monitor)
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass


@dataclasses.dataclass
class MonitorManager:
    """ Manage many website monitors at once, connect them to a publisher and scheduler.
    """

    monitors: Dict[str, WebsiteMonitor]
    publisher: publishers.BasePublisher
    scheduler: Optional[any] = None

    def run_all_monitors_once(self):
        asyncio.run(self.async_run_all_monitors_once())

    async def async_run_all_monitors_once(self):
        coroutines = (
            monitor.attempt_and_publish(self.publisher)
            for monitor in self.monitors.values()
        )
        await asyncio.gather(*coroutines)

    def schedule_all_monitors(self):
        assert not self.scheduler
        self.scheduler = SchedulerFacade(
            scheduler=AsyncIOScheduler(), publisher=self.publisher
        )
        for monitor in self.monitors.values():
            self.scheduler.schedule(monitor)
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

        filenames = (m.config_source for m in self.monitors.values() if m.config_source)
        for filename in filenames:
            monitor_updates.update(parse_websites_json(filename))

        if not monitor_updates:
            return

        for key, monitor in self.monitors.items():
            # Leave explicitly configured monitors alone
            if monitor.config_source is None:
                continue

            if key in monitor_updates:
                monitor.config = monitor_updates[key]
                self.scheduler.reschedule(monitor)
            else:
                self.scheduler.unschedule(monitor)
                del self.monitors[key]

        new_keys = set(monitor_updates) - set(self.monitors)
        for new_key in new_keys:
            new_monitor = WebsiteMonitor(monitor_updates[new_key])
            new_monitor.add_to_scheduler(self.scheduler, self.publisher)
            self.monitors[new_key] = new_monitor


def parse_websites_json(filename):
    if not filename:
        return

    with open(filename) as f:
        websites_data = json.load(f)

    for key, config in websites_data.items():
        if "url" not in config:
            config["url"] = key
        yield key, WebsiteMonitor(
            WebsiteMonitorConfig(**config), config_source=filename
        )
