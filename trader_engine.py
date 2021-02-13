import os
from abc import ABC
from typing import Any, Sequence, Type, Dict, List, Optional

from event_engine import Event, EventEngine
from trader_app import BaseApp
from trader_engine_email import EmailEngine
from trader_engine_omsengine import OmsEngine
from trader_event import (
    EVENT_LOG
)
from trader_gateway import BaseGateway
from trader_logging_engine import LogEngine
from trader_object import (
    CancelRequest,
    LogData,
    OrderRequest,
    SubscribeRequest,
    HistoryRequest,
    BarData,
    Exchange
)
from trader_utitlity import TRADER_DIR


class MainEngine:
    # core engine

    def __init__(self, event_engine: EventEngine = None):
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()

        self.event_engine.start()

        self.gateway: Dict[str, BaseGateway] = {}
        self.engines: Dict[str, BaseEngine] = {}
        self.apps: Dict[str, BaseApp] = {}
        self.exchanges: List[Exchange] = []

        os.chdir(TRADER_DIR)
        self.init_engines()

    def add_engine(self, engine_class: Any) -> "BaseEngine":
        engine = engine_class(self, self.event_engine)
        self.engines[self.gateway.gateway_name] = engine
        return engine

    def add_gateway(self, gateway_class: Type[BaseGateway]) -> BaseGateway:
        gateway = gateway_class(self.event_engine)
        self.gateways[gateway.gateway_name] = gateway

        for exchange in gateway.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return gateway

    def add_app(self, app_class: Type[BaseApp]) -> "BaseEngine":
        app = app_class()
        self.apps[app.app_name] = app

        engine = self.add_engine(app.engine_class)
        return engine

    def init_engines(self) -> None:
        self.add_engine(LogEngine)
        self.add_engine(OmsEngine)
        self.add_engine(EmailEngine)

    def write_log(self, msg: str, source: str = "") -> None:
        log = LogData(msg=msg, gateway_name=source)
        event = Event(EVENT_LOG, log)

        self.event_engine.put(event)

    def get_gateway(self, gateway_name: str) -> BaseGateway:
        gateway = self.gateway.get(gateway_name, None)
        if not gateway:
            self.write_log(f"找不到底层接口：{gateway_name}")
        return gateway

    def get_engine(self, engine_name: str) -> "BaseEngine":
        engine = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"找不到引擎：{engine_name}")
        return engine

    def get_default_setting(self, gateway_name: str) -> Optional[Dict[str, Any]]:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.get_default_setting()
        return None

    def get_all_gateway_names(self) -> List[str]:
        return list(self.gateway.keys())

    def get_all_apps(self) -> List[BaseApp]:
        return list(self.apps.values())

    def get_all_exchanges(self) -> List[Exchange]:
        return self.exchanges

    def connect(self, setting: dict, gateway_name: str) -> None:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.connect(setting)

    def subscribe(self, req: SubscribeRequest, gateway_name: str) -> None:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.subscribe(req)

    def send_order(self, req: OrderRequest, gateway_name: str) -> str:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_order(req)
        else:
            return ""

    def cancel_order(self, req: CancelRequest, gateway_name: str) -> None:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_order(req)

    def send_orders(self, reqs: Sequence[OrderRequest], gateway_name: str) -> List[str]:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.send_orders(reqs)
        else:
            return ["" for req in reqs]

    def cancel_orders(self, reqs: Sequence[CancelRequest], gateway_name: str) -> None:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            gateway.cancel_orders(reqs)

    def query_history(self, req: HistoryRequest, gateway_name: str) -> Optional[List[BarData]]:
        gateway = self.get_gateway(gateway_name)
        if gateway:
            return gateway.query_history(req)
        else:
            return None

    def close(self) -> None:
        self.event_engine.stop()

        for engine in self.engines.values():
            engine.close()
        for gateway in self.gateways.values():
            gateway.close()


