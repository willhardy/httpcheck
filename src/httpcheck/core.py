import asyncio
import json
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from . import publish
from .config import HttpMonitorConfig
from .monitor import HttpMonitor


def parse_websites_json(filename):
    with open(filename) as f:
        websites_data = json.load(f)

    for key, config in websites_data.items():
        if "url" not in config:
            config["url"] = key
        yield key, HttpMonitorConfig(**config)


def monitor_all(monitor_configs, kafka_config, websites_filename):
    monitor_configs_from_file = (
        dict(parse_websites_json(websites_filename)) if websites_filename else {}
    )
    all_monitor_configs = {**monitor_configs_from_file, **monitor_configs}
    publish_fn = publish.get_publish_fn(kafka_config)
    monitors = {}

    scheduler = AsyncIOScheduler()
    for key, config in all_monitor_configs.items():
        monitor = HttpMonitor(config)
        monitor.add_to_scheduler(scheduler, publish_fn)
        monitors[key] = monitor
    scheduler.start()

    def reload_config(signum, frame):
        seen = set()
        updates = dict(parse_websites_json(websites_filename))
        for key in monitors:
            if key in monitor_configs:
                pass
            elif key in updates:
                monitor = monitors[key]
                monitor.config = updates[monitor.config.url]
                monitor.update_scheduler()
            else:
                monitor = monitors[key]
                monitor.remove_from_scheduler()
                del monitors[key]
            seen.add(key)

        for new_key in set(updates) - seen:
            monitor = HttpMonitor(updates[new_key])
            monitor.add_to_scheduler(scheduler, publish_fn)
            monitors[new_key] = monitor

    signal.signal(signal.SIGHUP, reload_config)

    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
