from typing import Dict, Optional, List, Any

from event_engine import EventEngine, Event
from trader_engine_base import BaseEngine
from trader_event import EVENT_TICK, EVENT_TRADE, EVENT_ORDER, EVENT_POSITION, EVENT_ACCOUNT, EVENT_CONTRACT
from trader_object import TickData, OrderData, TradeData, PositionData, AccountData, ContractData


class OmsEngine(BaseEngine):
    # Provides order Management system function for vn trader
    def __init__(self, main_engine: Any, event_engine: EventEngine):
        super(OmsEngine, self).__init__(main_engine=main_engine, event_engine=event_engine, engine_name="oms")

        self.ticks: Dict[str, TickData] = {}
        self.orders: Dict[str, OrderData] = {}
        self.trades: Dict[str, TradeData] = {}
        self.positions: Dict[str, PositionData] = {}
        self.accounts: Dict[str, AccountData] = {}
        self.contracts: Dict[str, ContractData] = {}

        self.active_orders: Dict[str, OrderData] = {}

        self.add_function()
        self.register_event()

    def add_function(self) -> None:
        # add query function to main engine
        self.main_engine.get_tick = self.get_tick
        self.main_engine.get_order = self.get_order
        self.main_engine.get_trade = self.get_trade
        self.main_engine.get_position = self.get_position
        self.main_engine.get_account = self.get_account
        self.main_engine.get_contract = self.get_contract
        self.main_engine.get_all_ticks = self.get_all_ticks
        self.main_engine.get_all_orders = self.get_all_orders
        self.main_engine.get_all_trades = self.get_all_trades
        self.main_engine.get_all_positions = self.get_all_positions
        self.main_engine.get_all_accounts = self.get_all_accounts
        self.main_engine.get_all_contracts = self.get_all_contracts
        self.main_engine.get_all_active_orders = self.get_all_active_orders

    def register_event(self) -> None:
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)

    def process_tick_event(self, event: Event) -> None:
        tick: TickData = event.data
        self.ticks[tick.vt_symbol] = tick

    def process_order_event(self, event: Event) -> None:
        order: OrderData = event.data
        self.orders[order.vt_orderid] = order

        #         if order is active, update data in dict
        if order.is_active():
            self.active_orders[order.vt_orderid] = order
        elif order.vt_orderid in self.active_orders:
            self.active_orders.pop(order.vt_orderid)

    def process_trade_event(self, event: Event) -> None:
        trade: TradeData = event.data
        self.trades[trade.vt_tradeid] = trade

    def process_position_event(self, event: Event) -> None:
        position: PositionData = event.data
        self.positions[position.vt_postionid] = position

    def process_account_event(self, event: Event) -> None:
        account: AccountData = event.data
        self.accounts[account.vt_accountid] = account

    def process_contract_event(self, event: Event) -> None:
        contract: ContractData = event.data
        self.contracts[contract.vt_symbol] = contract

    def get_tick(self, vt_symbol: str) -> Optional[TickData]:
        # get latest tick data from vt_symbol
        return self.ticks.get(vt_symbol, None)

    def get_order(self, vt_orderid: str) -> Optional[OrderData]:
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid: str) -> Optional[TradeData]:
        return self.trades.get(vt_tradeid, None)

    def get_position(self, vt_positionid: str) -> Optional[PositionData]:
        return self.positions.get(vt_positionid, None)

    def get_account(self, vt_accountid: str) -> Optional[AccountData]:
        return self.accounts.get(vt_accountid, None)

    def get_contract(self, vt_symbol: str) -> Optional[ContractData]:
        return self.contracts.get(vt_symbol, None)

    def get_all_ticks(self) -> List[TickData]:
        return list(self.ticks.values())

    def get_all_orders(self) -> List[OrderData]:
        return list(self.orders.values())

    def get_all_trades(self) -> List[TradeData]:
        return list(self.trades.values())

    def get_all_positions(self) -> List[PositionData]:
        return list(self.positions.values())

    def get_all_accounts(self) -> List[AccountData]:
        return list(self.accounts.values())

    def get_all_contracts(self) -> List[ContractData]:
        return list(self.contracts.values())

    def get_all_active_orders(self, vt_symbol: str = "") -> List[OrderData]:
        if not vt_symbol:
            return list(self.active_orders.values())
        else:
            active_orders = [
                order
                for order in self.active_orders.values()
                if order.vt_symbol == vt_symbol
            ]
            return active_orders
