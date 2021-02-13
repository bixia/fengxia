from typing import Dict

import pytz

from event_engine import EventEngine, EVENT_TIMER, Event
from trader_constant import Direction, Exchange
from trader_gateway import BaseGateway
from trader_object import CancelRequest, OrderRequest, SubscribeRequest

REST_HOST = "https://1token.trade/api"

DIRECTION_VT2ONETOKEN = {
    Direction.LONG: "b",
    Direction.SHORT: "s"
}

DIRECTION_ONETOKEN2VT = {v: k for (k, v) in DIRECTION_VT2ONETOKEN.items()}

EXCHANGE_VT2ONETOKEN = {
    Exchange.OKEX: "okex",
    Exchange.HUOBI: "huobi",
    Exchange.BINANCE: "binance",
    Exchange.BITMEX: "bitmex",
    Exchange.GATEIO: "gateio",

}

CHINA_TZ = pytz.timezone("Asia/Shanghai")

exg_mapping = {
    "okex": "okex",
    "okef": "okex",
    "okswap": "okex",
    "huobip": "huobi",
    "huobiswap": "huobi",
    "binance": "binance",
    "binancef": "binance",
    "bitmex": "bitmex",
    "gate": "gateio"
}

EXCHANGE_ONETOKEN2VT = {v: k for (k, v) in EXCHANGE_VT2ONETOKEN.items()}


class OnetokenGateway(BaseGateway):
    default_setting = {
        "OT Key": "",
        "OT Secret": "",
        "交易所": ["BINANCE", 'OKEX', "OKEF", "HUOBIP", "HUOBIF"],
        "账户": "",
        "会话数": 3,
        "代理地址": "127.0.0.1",
        "代理端口": 1080,
    }

    exchanges = list(EXCHANGE_VT2ONETOKEN.keys())

    def __init__(self, event_engine: EventEngine):
        """
        继承自BaseGateway
        :param event_engine:
        """
        from gateway_1token_rest_client import OnetokenRestApi

        super(OnetokenGateway, self).__init__(event_engine=event_engine, gateway_name="1TOKEN")

        self.rest_api = OnetokenRestApi(self)

        self.count = 0

    def connect(self, setting: Dict) -> None:
        key = setting["OT Key"]
        secret = setting["OT Secret"]
        session_number = setting["会话数"]
        exchange = setting["交易所"].lower()
        account = setting["账户"]
        proxy_host = setting["代理地址"]
        proxy_port = setting["代理端口"]

        self.rest_api.connect(key, secret, session_number, exg_mapping.get(exchange), account, proxy_host, proxy_port)

        self.init_ping()

    def subscribe(self, req: SubscribeRequest) -> None:
        pass

    def send_order(self, req: OrderRequest) -> str:
        return self.rest_api.send_order(req)

    def cancel_order(self, req: CancelRequest) -> None:
        return self.rest_api.cancel_order(req)

    def query_account(self) -> None:
        pass

    def query_position(self) -> None:
        pass

    def close(self) -> None:
        self.rest_api.stop()

    def process_timer_event(self, event: Event):
        self.count += 1
        if self.count < 20:
            return
        self.count = 0

        print("PING PONG every 20 seconds")

    def init_ping(self):
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)
