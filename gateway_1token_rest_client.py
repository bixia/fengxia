import hashlib
import hmac
import json
import time
from datetime import datetime
from threading import Lock
from urllib.parse import urlparse

from api_rest_client import RestClient, Request
from gateway_1token_base import CHINA_TZ, REST_HOST, DIRECTION_VT2ONETOKEN
from trader_constant import Exchange, Product, Offset, Status
from trader_gateway import BaseGateway
from trader_object import ContractData, OrderRequest, CancelRequest


class OnetokenRestApi(RestClient):
    # 1token rest api
    def __init__(self, gateway: BaseGateway):
        super(OnetokenRestApi, self).__init__()
        self.gateway: BaseGateway = gateway
        self.gateway_name: str = gateway.gateway_name

        self.key = ""
        self.secret = ""
        self.exchange = ""

        self.order_count = 1_000_000
        self.order_count_lock = Lock()

        self.connect_time = 0
        self.account = ""

    def sign(self, request: Request) -> Request:
        """
        Generate 1Token signature
        :param request:
        :return:
        """
        method = request.method

        endpoint = "/" + request.path.split("/", 3)[3]
        #         v1/trade/okex/mock-example/info -> okex/mock-example/info
        parsed_url = urlparse(endpoint)
        path = parsed_url.path

        nonce = str(int(time.time() * 1e6))
        data = request.data
        json_str = data if data else ""

        message = method + path + nonce + json_str

        signature = hmac.new(bytes(self.secret, "utf8"), bytes(message, "utf8"), digestmod=hashlib.sha256).hexdigest()

        headers = {
            "Api-Nonce": nonce,
            "Api-key": self.key,
            "Api-Signature": signature,
            "Content-Type": "application/json"
        }

        request.headers = headers

        return request

    def connect(
            self,
            key: str,
            secret: str,
            session_number: int,
            exchange: str,
            account: str,
            proxy_host: str,
            proxy_port: int,
    ) -> None:
        """
        initialize connection to rest server
        :param key:
        :param secret:
        :param session_number:
        :param exchange:
        :param account:
        :param proxy_host:
        :param proxy_port:
        :return:
        """
        self.key = key
        self.secret = secret
        self.exchange = exchange
        self.account = account
        self.connect_time = int(datetime.now(CHINA_TZ).strftime("%y%m%d%H%M%S")) * self.order_count

        self.init(REST_HOST, proxy_host, proxy_port)

        self.start(session_number)

        self.gateway.write_log("REST API 启动成功")

        self.query_time()
        self.query_contract()

    def _new_order_id(self) -> int:
        with self.order_count_lock:
            self.order_count += 1
            return self.order_count

    def query_time(self) -> None:
        """
        check whether connected
        :return:
        """
        self.add_request(
            "GET",
            "/v1/basic/time",
            callback=self.on_query_time
        )

    def on_query_time(self, data: dict, request: Request) -> None:
        """
        handle query time
        :param data:
        :param request:
        :return:
        """
        print(data)
        server_timestamp = data["server_time"]
        dt = datetime.utcfromtimestamp(server_timestamp)
        server_time = dt.isoformat() + "Z"
        local_time = datetime.utcnow().isoformat()
        msg = f"服务器时间：{server_time},本机时间：{local_time}"
        print(msg)
        self.gateway.write_log(msg)

    def query_contract(self) -> None:
        """
        query contract
        :return:
        """

        self.add_request(
            "GET",
            "/v1/basic/contract?exchange={}".format(self.exchange),
            callback=self.on_query_contract

        )

    def on_query_contract(self, data: dict, reqeust: Request) -> None:
        """

        :param data:
        :param reqeust:
        :return:
        """
        for instrument_data in data:
            symbol = instrument_data["name"]
            contract = ContractData(
                symbol=symbol,
                exchange=Exchange(instrument_data['symbol'].split('/')[0].upper()),
                name=symbol,
                product=Product.SPOT,
                size=float(instrument_data["min_amount"]),
                pricetick=float(instrument_data["unit_amount"]),
                gateway_name=self.gateway_name,
            )
            self.gateway.on_contract(contract)
        self.gateway.write_log("合约信息查询成功")

    def send_order(self, req: OrderRequest) -> str:
        """

        :param req:
        :return:
        """

        orderid = str(self.connect_time + self._new_order_id())
        data = {
            "contract": self.exchange + "/" + req.symbol,
            "price": float(req.price),
            "bs": DIRECTION_VT2ONETOKEN(req.direction),
            "amount": float(req.volume),
            "client_oid": orderid
        }

        if req.offset == Offset.CLOSE:
            data["options"] = {"close": True}

        data = json.dumps(data)
        order = req.create_order_data(orderid, self.gateway_name)

        self.add_request(
            method="POST",
            path="/v1/trade/{}/{}/orders".format(self.exchange, self.account),
            callback=self.on_send_order,
            data=data,
            params={},
            extra=order,
            on_failed=self.on_send_order_failed,
            on_error=self.on_send_order_error,
        )

        self.gateway.on_order(order)
        return order.orderid

    def cancel_order(self, req: CancelRequest):
        """

        :param req:
        :return:
        """
        params: dict = {
            "client_oid": req.orderid
        }
        self.add_request(
            method="POST",
            path="/v1/trade/{}/{}/orders".format(self.exchange, self.account),
            callback=self.on_cancel_order,
            params=params,
            on_error=self.on_cancel_order_error,
            extra=req
        )

    def on_send_order(self, data: dict, request: Request) -> None:
        print(data)

    def on_send_order_failed(self, status_code: str, request: Request) -> None:
        """
        callback when sending order failed on server
        :param status_code:
        :param request:
        :return:
        """

        order = request.extra
        order.status = Status.REJECTED
        self.gateway.on_order(order)

        msg = f"委托失败，状态码:{status_code}, 信息：{request.response.text}"
        self.gateway.write_log(msg)

    def on_send_order_error(self, exception_type: type, exception_value: Exception, tb, request: Request) -> None:
        """
        callback when error
        :param exception_type:
        :param exception_value:
        :param tb:
        :param request:
        :return:
        """

        order = request.extra
        order.status = Status.REJECTED
        self.gateway.on_order(order)

        if not issubclass(exception_type, ConnectionError):
            self.on_error(exception_type, exception_value, tb, request)

    def on_cancel_order(self, data: dict, request: Request) -> None:
        print(data)

    def on_cancel_order_error(self, exception_type: type, exception_value: Exception, tb, request: Request) -> None:
        """

        :param exception_type:
        :param exception_value:
        :param tb:
        :param request:
        :return:
        """
        if not issubclass(exception_type, ConnectionError):
            self.on_error(exception_type, exception_value, tb, request)
