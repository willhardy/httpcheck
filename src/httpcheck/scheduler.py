import dataclasses
import typing

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import BaseScheduler


@dataclasses.dataclass(frozen=True)
class Scheduler:
    """A Facade providing simplified access to the implementation (apscheduler)
    """

    job_fn: typing.Callable
    scheduler: BaseScheduler = dataclasses.field(default_factory=AsyncIOScheduler)

    def start(self):
        self.scheduler.start()

    def _get_job_id(self, monitor_config):
        key = monitor_config.key or monitor_config.url
        return f"httpcheck:{key}"

    def run_once(self, monitor_config):
        self.scheduler.add_job(self.job_fn, args=[monitor_config])

    def schedule(self, monitor_config):
        job_id = self._get_job_id(monitor_config)

        # Run immediately, AsyncScheduler does not start with an immediate job
        self.run_once(monitor_config)

        # Schedule repeats
        self.scheduler.add_job(
            self.job_fn,
            trigger="interval",
            seconds=monitor_config.frequency,
            args=[monitor_config],
            id=job_id,
            replace_existing=True,
        )

    def reschedule(self, monitor_config):
        job_id = self._get_job_id(monitor_config)
        try:
            self.scheduler.reschedule_job(
                job_id, trigger="interval", seconds=monitor_config.frequency
            )
        except JobLookupError:
            self.schedule(monitor_config)

    def unschedule(self, monitor_config):
        job_id = self._get_job_id(monitor_config)
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass
