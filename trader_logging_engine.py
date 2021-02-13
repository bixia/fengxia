import logging
from datetime import datetime
from logging import Logger
from typing import Any

from event_engine import Event, EventEngine
from trader_engine_base import BaseEngine
from trader_event import EVENT_LOG
from trader_setting import SETTINGS
from trader_utitlity import get_folder_path


class LogEngine(BaseEngine):
    def __init__(self, main_engine: Any, event_engine: EventEngine):
        super(LogEngine, self).__init__(main_engine=main_engine, event_engine=event_engine, engine_name="log")

        if not SETTINGS['log.active']:
            return

        self.level: int = SETTINGS['log.level']

        self.logger: Logger = logging.getLogger("fengxia")
        self.logger.setLevel(self.level)

        self.formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s"
        )
        self.add_null_handler()

        if SETTINGS["log.console"]:
            self.add_console_handler()
        if SETTINGS["log.file"]:
            self.add_file_handler()

        self.register_event()

    def add_null_handler(self) -> None:
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)

    def add_console_handler(self) -> None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def add_file_handler(self) -> None:
        today_date = datetime.now().strftime("%Y%m%d")
        filename = f"fx_{today_date}.log"
        log_path = get_folder_path(filename)
        file_path = log_path.joinpath(filename)

        file_handler = logging.FileHandler(
            file_path, mode="a", encoding="utf8"
        )
        file_handler.setLevel(self.level)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def register_event(self) -> None:
        self.event_engine.register(EVENT_LOG, self.process_log_event)

    def process_log_event(self, event: Event) -> None:
        log = event.data
        self.logger.log(log.level, log.msg)
