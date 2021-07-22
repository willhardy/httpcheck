import dataclasses
import logging


logger = logging.getLogger(__name__)
REGISTERED_PUBLISHERS = {}


def get_publisher(config):
    backend = config.pop("backend")
    return REGISTERED_PUBLISHERS[backend](config)


class BasePublisher:
    """ Class that provides a .publish() method that will publish the results.
    """

    key = None

    @dataclasses.dataclass(frozen=True)
    class Config:
        pass

    def __init__(self, config):
        relevant_config_keys = {f.name for f in dataclasses.fields(self.Config)}
        relevant_config = {k: v for k, v in config.items() if k in relevant_config_keys}
        self.config = self.Config(**relevant_config)

    def publish(self, msg):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __init_subclass__(cls, **kwargs):
        REGISTERED_PUBLISHERS[cls.key] = cls
        super().__init_subclass__(**kwargs)


class ConsolePublisher(BasePublisher):
    key = "console"

    def publish(self, data):
        print(data, flush=True)
