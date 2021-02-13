from dataclasses import dataclass
from datetime import datetime
from logging import INFO

from trader_constant import Direction, Exchange, Interval, Offset, Status, Product, OptionType, OrderType

ACTIVE_STATUSES = set([Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED])


@dataclass
class BaseData:
    gateway_name: str


@dataclass
class TickData(BaseData):
    symbol: str
    exchange: Exchange
    datetime: datetime

    name: str = ""
    volume: float = 0
    open_interest: float = 0
    last_price: float = 0
    last_volume: float = 0
    limit_up: float = 0
    limit_down: float = 0

    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    pre_close: float = 0

    bid_price_1: float = 0
    bid_price_2: float = 0
    bid_price_3: float = 0
    bid_price_4: float = 0
    bid_price_5: float = 0

    ask_price_1: float = 0
    ask_price_2: float = 0
    ask_price_3: float = 0
    ask_price_4: float = 0
    ask_price_5: float = 0

    bid_volume_1: float = 0
    bid_volume_2: float = 0
    bid_volume_3: float = 0
    bid_volume_4: float = 0
    bid_volume_5: float = 0

    ask_volume_1: float = 0
    ask_volume_2: float = 0
    ask_volume_3: float = 0
    ask_volume_4: float = 0
    ask_volume_5: float = 0

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class BarData(BaseData):
    symbol: str
    exchange: Exchange
    datetime: datetime

    interval: Interval = None
    volume: float = 0
    open_interest: float = 0
    open_price: float = 0
    high_price: float = 0
    low_price: float = 0
    close_price: float = 0

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderData(BaseData):
    symbol: str
    exchange: Exchange
    orderid: str

    type: OrderType = OrderType.LIMIT
    direction: Direction = None
    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    traded: float = 0
    status: Status = Status.SUBMITTING
    datetime: datetime = None
    reference: str = ""

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"

    def is_active(self) -> bool:
        if self.status in ACTIVE_STATUSES:
            return True
        else:
            return False

    def create_cancel_request(self) -> "CancelRequest":
        req = CancelRequest(
            orderid=self.orderid, symbol=self.symbol, exchang=self.exchange
        )
        return req


@dataclass
class TradeData(BaseData):
    symbol: str
    exchange: Exchange
    orderid: str
    tradeid: str
    direction: Direction = None

    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    datetime: datetime = None

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"
        self.vt_tradeid = f"{self.gateway_name}.{self.tradeid}"


@dataclass
class PositionData(BaseData):
    symbol: str
    exchange: Exchange
    direction: Direction

    volume: float = 0
    frozen: float = 0
    price: float = 0
    pnl: float = 0
    yd_volume: float = 0

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_postionid = f"{self.vt_symbol}.{self.direction.value}"


@dataclass
class AccountData(BaseData):
    accountid: str

    balance: float = 0
    frozen: float = 0

    def __post_init__(self):
        self.available = self.balance - self.frozen
        self.vt_accountid = f"{self.gateway_name}.{self.accountid}"


@dataclass
class LogData(BaseData):
    msg: str
    level: int = INFO

    def __post_init__(self):
        self.time = datetime.now()


@dataclass
class ContractData(BaseData):
    symbol: str
    exchange: Exchange
    name: str
    product: Product
    size: float
    pricetick: float

    min_volume: float = 1
    stop_supported: bool = False
    net_position: bool = False
    history_data: bool = False

    option_strike: float = 0
    option_underlying: str = ""
    option_type: OptionType = None
    option_expiry: datetime = None
    option_portfolio: str = ""
    option_index: str = ""

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class SubscribeRequest:
    symbol: str
    exchange: Exchange

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderRequest:
    symbol: str
    exchange: Exchange
    direction: Direction
    type: OrderType
    volume: float
    price: float = 0
    offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"

    def create_order_data(self, orderid: str, gateway_name: str) -> OrderData:
        order = OrderData(
            symbol=self.symbol,
            exchange=self.exchange,
            orderid=orderid,
            type=self.type,
            gateway_name=gateway_name,
            direction=self.direction,
            offset=self.offset,
            price=self.price,
            volume=self.volume,
            reference=self.reference
        )
        return order


@dataclass
class CancelRequest:
    orderid: str
    symbol: str
    exchange: Exchange

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


@dataclass
class HistoryRequest:
    symbol: str
    exchange: Exchange
    start: datetime
    end: datetime = None
    interval: Interval = None

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
