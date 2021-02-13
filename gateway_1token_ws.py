import sys
from copy import copy
from datetime import datetime

from api_web_socket import WebsocketClient
from gateway_1token_base import CHINA_TZ
from gateway_huobi import generate_datetime
from trader_gateway import BaseGateway
from trader_object import SubscribeRequest, TickData

DATA_WEBSOCKET_HOST = "wss://cdn.1tokentrade.cn/api/v1/ws/tick"
TRADE_WEBSOCKET_HOST = "wss://cdn.1tokentrade.cn/api/v1/ws/trade"


class OnetokenDataWebsocketApi(WebsocketClient):
    def __init__(self, gateway: BaseGateway):
        super(OnetokenDataWebsocketApi, self).__init__()

        self.gateway: BaseGateway = gateway
        self.gateway_name = gateway.gateway_name
        self.subscribed = {}
        self.ticks = {}
        self.callbacks = {
            "auth": self.on_login,
            "single-tick-verbose": self.on_tick
        }

    def connect(self,
                proxy_host: str,
                proxy_port: int
                ):
        self.init(DATA_WEBSOCKET_HOST, proxy_host, proxy_port)

    def subscribe(self, req: SubscribeRequest):
        """
        Subscribe to tick data update
        :param req:
        :return:
        """
        self.subscribed[req.vt_symbol] = req
        tick: TickData = TickData(
            symbol=req.symbol,
            exchange=req.exchange,
            name=req.symbol,
            datetime=datetime.now(CHINA_TZ),
            gateway_name=self.gateway_name,
        )

        contract_symbol = f"{req.exchange.value.lower()}/{req.symbol.lower()}"
        self.ticks[contract_symbol] = tick

        req = {
            "uri": "subscribe-single-tick-verbose",
            "contract": contract_symbol,
        }
        self.send_packet(req)

    def on_connected(self):
        self.gateway.write_log("行情websocket API 链接成功")
        self.login()

    def on_disconnected(self):
        self.gateway.write_log("行情Websocket API 链接断开")

    def on_packet(self, packet: dict):
        channel = packet.get("uri", "")
        if not channel:
            return
        data = packet.get("data", None)
        callback = self.callbacks.get(channel, None)
        if callback:
            callback(data)

    def on_error(self, exception_type: type, exception_value: Exception, tb):
        msg = f"触发异常，状态码：{exception_type}, 信息：{exception_value}"
        self.gateway.write_log(msg)

        sys.stderr.write(self.exception_detail(
            exception_type, exception_value, tb
        ))

    def login(self):
        req = {"uri": "auth"}
        self.send_packet(req)
        self.callbacks["auth"] = self.on_login

    def on_login(self, data: dict):
        self.gateway.write_log("行情Wensocket API 登录成功")
        for req in list(self.subscribed.values()):
            self.subscribe(req)

    def on_tick(self, data: dict):
        contract_symbol = data["contract"]
        tick: TickData = self.ticks.get(contract_symbol, None)
        if not tick:
            return
        tick.last_price = data["last"]
        tick.datetime = generate_datetime(data["time"][:-6])

        bids = data["bids"]
        asks = data["asks"]

        for n, buf in enumerate(bids):
            tick.__setattr__("bid_price_%s" % (n + 1), buf["price"])
            tick.__setattr__("bid_volume_%s" % (n + 1), buf["volume"])
        for n, buf in enumerate(asks):
            tick.__setattr__("ask_price_%s" % (n + 1), buf["price"])
            tick.__setattr__("ask_volume_%s" % (n + 1), buf["volume"])
        self.gateway.on_tick(copy(tick))

    def ping(self):
        self.send_packet({"uri": "ping"})