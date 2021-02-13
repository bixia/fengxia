import base64
import hashlib
import hmac
import json
import re
import sys
import urllib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import pytz

from api_rest_client import RestClient, Request
from event_engine import EventEngine
from gateway_huobi_rest_client import HuobiRestApi
from trader_constant import (
    Direction,
    Exchange,
    Product,
    Status,
    OrderType,
    Interval
)
from trader_gateway import BaseGateway
from trader_object import (
    OrderData,
    ContractData,
    BarData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    HistoryRequest
)

REST_HOST = "http://api.huobipro.com"

STATUS_HUOBI2VT = {
    "submitted": Status.NOTTRADED,
    "partial-filled": Status.PARTTRADED,
    "filled": Status.ALLTRADED,
    "cancelling": Status.CANCELLED,
    "partial-canceled": Status.CANCELLED,
    "canceled": Status.CANCELLED
}

ORDERTYPE_VT2HUOBI = {
    (Direction.LONG, OrderType.MARKET): "buy-market",
    (Direction.SHORT, OrderType.MARKET): "sell-market",
    (Direction.LONG, OrderType.LIMIT): "buy-limit",
    (Direction.SHORT, OrderType.LIMIT): "sell-limit",
}

ORDERTYPE_HUOBI2VT = {v: k for (k, v) in ORDERTYPE_VT2HUOBI}

INTERVAL_VT2HUOBI = {
    Interval.MINUTE: "1min",
    Interval.HOUR: "60min",
    Interval.DAILY: "1day",
}

CHINA_TZ = pytz.timezone("Asia/Shanghai")

huobi_symbols: set = set()
symbol_name_map: Dict[str, str] = {}
current_balance: Dict[str, float] = {}


def generate_datetime(timestamp: float) -> datetime:
    dt = datetime.fromtimestamp(timestamp)
    dt = CHINA_TZ.localize(dt)
    return dt


def create_signature(
        api_key: str,
        method: str,
        host,
        path,
        secret_key,
        get_params: Dict = None
) -> Dict[str, str]:
    """
    创建签名 get_params : dict
    :param api_key:
    :param method:
    :param host:
    :param path:
    :param secret_key:
    :param get_params:
    :return:
    """
    sorted_params = [
        ("AccessKeyId", api_key),
        ("SignatureMethod", "HmacSHA256"),
        ("SignatureVersion", "2"),
        ("Timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    ]

    if get_params:
        sorted_params.extend(list(get_params.items()))
        sorted_params = list(sorted(sorted_params))
    encode_params = urllib.parse.urlencode(sorted_params)

    payload = [method, host, path, encode_params]
    payload = "\n".join(payload)
    payload = payload.encode(encoding="UTF-8")

    secret_key = secret_key.encode(encoding="UTF-8")

    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)

    params = dict(sorted_params)
    params["Signature"] = signature.decode("UTF8")
    return params


def _split_url(url: str) -> Tuple[str, str]:
    """
    将URL 拆分为 host和path
    :param url:
    :return: host, path
    """
    result = re.match("\w+//([^/]*)(.*)", url)
    if result:
        return result.group(1), result.group(2)


class HuobiGateWay(BaseGateway):
    default_setting: Dict[str, Any] = {
        "API Key": "",
        "Secret Key": "",
        "会话数": 3,
        "代理地址": "",
        "代理接口": "",
    }

    exchanges: List[Exchange] = [Exchange.HUOBI]

    def __init__(self, event_engine: EventEngine):
        super(HuobiGateWay, self).__init__(event_engine=event_engine, gateway_name="HUOBI")

        self.rest_api = HuobiRestApi(self)

        self.orders: Dict[str, OrderData] = {}

    def get_order(self, orderid: str) -> Optional[OrderData]:
        return self.orders.get(orderid, None)

    def on_order(self, order: OrderData) -> None:
        self.orders[order.orderid] = order
        super(HuobiGateWay, self).on_order(order)

    def connect(self, setting: Dict) -> None:
        key = setting["API Key"]
        secret = setting["Secret Key"]
        session_number = setting["会话数"]
        proxy_host = setting["代理地址"]
        proxy_port = setting["代理端口"]

        if proxy_port.isdigit():
            proxy_port = int(proxy_port)
        else:
            proxy_port = 0

        self.rest_api.connect(key, secret, session_number, proxy_host, proxy_port)

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

    def query_history(self, req: HistoryRequest) -> Optional[List[BarData]]:

        return self.rest_api.query_history(req)

    def close(self) -> None:
        self.rest_api.stop()

