from abc import ABC, abstractclassmethod
from typing import Any, Dict, List

from event_engine import Event, EventEngine
from trader_event import (
    EVENT_TICK,
    EVENT_ORDER,
    EVENT_TRADE,
    EVENT_POSITION,
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_LOG,
)
from trader_object import (
    TickData,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    LogData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    HistoryRequest,
    Exchange
)


class BaseGateway(ABC):
    default_setting: Dict[str, Any] = {}
    exchanges: List[Exchange] = []

    def __init__(self, event_engine: EventEngine, gateway_name: str):
        """"""

        self.event_engine: EventEngine = event_engine
        self.gateway_name: str = gateway_name

    def on_event(self, type: str, data: Any = None) -> None:
        event = Event(type, data)
        self.event_engine.put(event)

    def on_tick(self, tick: TickData) -> None:

        self.on_event(EVENT_TICK, tick)
        self.on_event(EVENT_TICK + tick.vt_symbol, tick)

    def on_trade(self, trade: TradeData) -> None:
        self.on_event(EVENT_TRADE, trade)
        self.on_event(EVENT_TRADE + trade.vt_symbol, trade)

    def on_order(self, order: OrderData) -> None:
        self.on_event(EVENT_ORDER, order)
        self.on_event(EVENT_ORDER + order.vt_orderid, order)

    def on_position(self, position: PositionData) -> None:
        self.on_event(EVENT_POSITION, position)
        self.on_event(EVENT_POSITION + position.vt_symbol, position)

    def on_account(self, account: AccountData) -> None:
        self.on_event(EVENT_ACCOUNT, account)
        self.on_event(EVENT_ACCOUNT + account.vt_accountid, account)

    def on_log(self, log: LogData) -> None:
        self.on_event(EVENT_LOG, log)

    def on_contract(self, contract: ContractData) -> None:
        self.on_event(EVENT_CONTRACT, contract)

    def write_log(self, msg: str) -> None:
        log = LogData(gateway_name=self.gateway_name, msg=msg)
        self.on_log(log)

    @abstractclassmethod
    def connect(self, setting: Dict) -> None:
        pass

    @abstractclassmethod
    def close(self) -> None:
        pass

    @abstractclassmethod
    def subscribe(self, req: SubscribeRequest) -> None:
        pass

    @abstractclassmethod
    def send_order(self, req: OrderRequest) -> str:
        pass

    @abstractclassmethod
    def cancel_order(self, req: CancelRequest) -> None:
        pass

    def send_orders(self, reqs: List[OrderRequest]) -> List[str]:
        vt_orderids = []
        for req in reqs:
            vt_orderid = self.send_order(req)
            vt_orderids.append(vt_orderid)

        return vt_orderids

    def cancel_orders(self, reqs: List[CancelRequest]) -> None:
        for req in reqs:
            self.cancel_order(req)

    @abstractclassmethod
    def query_account(self) -> None:
        pass

    @abstractclassmethod
    def query_position(self) -> None:
        pass

    def query_history(self, req: HistoryRequest) -> None:
        pass

    def get_default_setting(self) -> Dict[str, Any]:
        return self.default_setting
