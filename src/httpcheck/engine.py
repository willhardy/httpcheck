import json
import logging
import signal

import httpcheck


logger = logging.getLogger(__name__)


def load_monitor_configs_from_websites_file(websites_filename):
    # 1. Generate the config for each website listed in the --websites JSON file
    monitor_configs = {}
    with open(websites_filename) as f:
        websites_data = json.load(f)
    for key, config in websites_data.items():
        if "url" not in config:
            config["url"] = key
        monitor_configs[key] = httpcheck.HttpMonitorConfig(**config)
    return monitor_configs


async def monitor_all(monitor_configs, websites_file, kafka_config):
    monitor_configs_from_file = load_monitor_configs_from_websites_file(websites_file)
    all_monitor_configs = {**monitor_configs_from_file, **monitor_configs}

    tasks = []
    for _, config in all_monitor_configs.items():
        monitor = httpcheck.HttpMonitor(config)
        task = monitor.get_asyncio_task(kafka_config)
        tasks.append((monitor, task))

    def reload_config(signum, frame):
        logger.debug(f"****** Signal {signum} caught")
        new_monitor_configs = load_monitor_configs_from_websites_file(websites_file)
        all_monitor_configs = {**new_monitor_configs, **monitor_configs}

        for _, task in tasks:
            task.cancel()
        tasks[:] = []
        for _, config in all_monitor_configs.items():
            monitor = httpcheck.HttpMonitor(config)
            task = monitor.get_asyncio_task(kafka_config)
            tasks.append((monitor, task))

    signal.signal(signal.SIGHUP, reload_config)

    logger.debug("****** Starting tasks")
    for _, task in tasks:
        await task
