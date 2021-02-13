from abc import ABC
from typing import Any

from event_engine import EventEngine


# from trader_engine import MainEngine


class BaseEngine(ABC):
    def __init__(
            self,
            main_engine: Any,
            event_engine: EventEngine,
            engine_name: str,
    ):
        self.main_engine = main_engine
        self.event_engine = event_engine
        self.engine_name = engine_name

    def close(self):
        pass
