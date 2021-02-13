import json
import sys
from datetime import datetime
from typing import List, Optional

from api_rest_client import RestClient, Request
from gateway_huobi import create_signature, REST_HOST, _split_url, INTERVAL_VT2HUOBI, generate_datetime, \
    ORDERTYPE_VT2HUOBI, CHINA_TZ, ORDERTYPE_HUOBI2VT, STATUS_HUOBI2VT, huobi_symbols, symbol_name_map
from trader_constant import Exchange, Product, Status
from trader_gateway import BaseGateway
from trader_object import HistoryRequest, BarData, OrderRequest, CancelRequest, OrderData, ContractData


class HuobiRestApi(RestClient):

    def __init__(self, gateway: BaseGateway):
        super(HuobiRestApi, self).__init__()

        self.gateway: BaseGateway = gateway
        self.gateway_name: str = gateway.gateway_name

        self.host: str = ""
        self.key: str = ""
        self.secret: str = ""
        self.account_id: str = ""

        self.order_count: int = 0

    def new_orderid(self) -> str:
        prefix = datetime.now().strftime("%Y%m%d-%H%M%S-")

        self.order_count += 1
        suffix = str(self.order_count).rjust(8, "0")

        orderid = prefix + suffix
        return orderid

    def sign(self, request: Request) -> Request:

        request.headers = {
            "User-Agent": "Mozilla\5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.6"
        }

        params_with_signature = create_signature(
            self.key,
            request.method,
            self.host,
            request.path,
            self.secret,
            request.params
        )
        request.params = params_with_signature

        if request.method == "POST":
            request.headers["Content-Type"] = "application\json"

            if request.data:
                request.data = json.dumps(request.data)
        return request

    def connect(
            self,
            key: str,
            secret: str,
            session_number: int,
            proxy_host: str,
            proxy_port: int
    ) -> None:
        self.key = key
        self.secret = secret

        self.host, _ = _split_url(REST_HOST)

        self.init(REST_HOST, proxy_host, proxy_port)
        self.start(session_number)

        self.gateway.write_log("REST API 启动成功")

        self.query_contract()
        self.query_account()
        self.query_order()

    def query_account(self) -> None:
        self.add_request(method="Get", path="/v1/account/accounts", callback=self.on_query_account)

    def query_order(self) -> None:

        self.add_request(method="Get", path="/v1/order/openOrders", callback=self.on_query_order)

    def query_contract(self) -> None:
        self.add_request(method="Get", path="/v1/common/symbols", callback=self.on_query_contract)

    def query_history(self, req: HistoryRequest) -> List[BarData]:
        params = {
            "symbol": req.symbol,
            "period": INTERVAL_VT2HUOBI[req.interval],
            "size": 2000
        }
        resp = self.request(
            method='Get',
            path="/market/history/kline",
            params=params
        )

        history = []
        if resp.status_code // 100 != 2:
            msg = f"获取历史数据失败，状态码：{resp.status_code}, 信息：{resp.text}"
            self.gateway.write_log(msg)
        else:
            data = resp.json()
            if not data:
                msg = f"获取历史数据为空"
                self.gateway.write_log(msg)
            else:
                for d in data["data"]:
                    dt = generate_datetime(d["id"])

                    bar = BarData(
                        symbol=req.symbol,
                        exchange=req.exchange,
                        datetime=dt,
                        interval=req.interval,
                        volume=d["vol"],
                        open_price=d["open"],
                        high_price=d["high"],
                        low_price=d["low"],
                        close_price=d["close"],
                        gateway_name=self.gateway_name
                    )
                    history.append(bar)

                history.reverse()
                begin = history[0].datetime
                end = history[-1].datetime
                msg = f"获取历史数据成功，{req.symbol} - {req.interval.value}, {begin} - {end}"
                self.gateway.write_log(msg)

        return history

    def send_order(self, req: OrderRequest) -> str:
        huobi_type = ORDERTYPE_VT2HUOBI.get(
            (req.direction, req.type), ""
        )
        orderid = self.new_orderid()
        order = req.create_order_data(orderid, self.gateway_name)
        order.datetime = datetime.now(CHINA_TZ)

        data = {
            "account-id": self.account_id,
            "amount": str(req.volume),
            "symbol": req.symbol,
            "type": huobi_type,
            "price": str(req.price),
            "source": "api",
            "client_order_id": orderid
        }
        self.add_request(
            method="POST",
            path="/v1/order/orders/place",
            callback=self.on_send_order,
            data=data,
            extra=order,
            on_error=self.on_send_order_error,
            on_failed=self.on_send_order_failed
        )
        self.gateway.on_order(order)
        return order.vt_orderid

    def cancel_order(self, req: CancelRequest) -> None:
        data = {"client-order-id": req.orderid}
        self.add_request(
            method="POST",
            path="/v1/order/orders/submitCancelClientOrder",
            data=data,
            callback=self.on_cancel_order,
            extra=req
        )

    def on_query_account(self, data: dict, requst: Request) -> None:
        if self.check_error(data, "查询账户"):
            return

        for d in data["data"]:
            if d["type"] == "spot":
                self.account_id = d["id"]
                self.gateway.write_log(f"账户代码{self.account_id}查询成功")

    def on_query_order(self, data: dict, request: Request) -> None:
        if self.check_error(data, "查询委托"):
            return

        for d in data["data"]:
            direction, order_type = ORDERTYPE_HUOBI2VT[d["type"]]
            dt = generate_datetime(d["created-at"] / 1000)

            order = OrderData(
                orderid=d["client-order-id"],
                symbol=d["symbol"],
                exchange=Exchange.HUOBI,
                price=float(d["price"]),
                volume=float(d["amount"]),
                type=order_type,
                direction=direction,
                traded=STATUS_HUOBI2VT.get(d["state"], None),
                datetime=dt,
                gateway_name=self.gateway_name,
            )

            self.gateway.on_order(order)

        self.gateway.write_log("委托查询成功")

    def on_query_contract(self, data: dict, request: Request) -> None:
        if self.check_error(data, "查询合约"):
            return
        for d in data["data"]:
            base_currency = d["base-currency"],
            quote_currency = d["quote-currency"]
            name = f"{base_currency.upper()}/{quote_currency.upper()}"
            pricetick = 1 / pow(10, d["price-precision"])
            min_volume = 1 / pow(10, d["amount-precision"])

            contract = ContractData(
                symbol=d["symbol"],
                exchange=Exchange.HUOBI,
                name=name,
                pricetick=pricetick,
                size=1,
                min_volume=min_volume,
                product=Product.SPOT,
                history_data=True,
                gateway_name=self.gateway_name
            )
            self.gateway.on_contract(contract)

            huobi_symbols.add(contract.symbol)
            symbol_name_map[contract.symbol] = contract.name

        self.gateway.write_log("合约信息查询成功")

    def on_send_order(self, data: dict, request: Request) -> None:
        order = request.extra

        if self.check_error(data, "委托"):
            order.status = Status.REJECTED
            self.gateway.on_order(order)

    def on_send_order_failed(self, status_code: dict, request: Request) -> None:
        order = request.extra
        order.status = Status.REJECTED
        self.gateway.on_order(order)

        msg = f"委托失败，状态码：{status_code},信息：{request.response.text}"
        self.gateway.write_log(msg)

    def on_send_order_error(self, exception_type: type, exception_value: Exception, tb, request: Request) -> None:
        order = request.extra
        order.status = Status.REJECTED
        self.gateway.on_order(order)

        if not issubclass(exception_type, ConnectionError):
            self.on_error(exception_type, exception_value, tb, request)

    def on_cancel_order(self, data: dict, request: Request) -> None:
        cancel_request = request.extra
        order: OrderData = self.gateway.get_order(cancel_request.orderid)
        if not order:
            return
        if self.check_error(data, "撤单"):
            order.status = Status.REJECTED
        else:
            order.status = Status.CANCELLED
            self.gateway.write_log(f"委托撤单成功：{order.orderid}")

        self.gateway.on_order(order)

    def on_error(
            self,
            exception_type: type,
            exception_value: Exception,
            tb,
            request: Request
    ) -> None:
        """

        :param exception_type:
        :param exception_value:
        :param tb:
        :param request:
        :return:

        callback to handler request exception
        """
        msg = f"触发异常，状态码:{exception_type}, 信息：{exception_value}"
        self.gateway.write_log(msg)

        sys.stderr.write(
            self.exception_detail(exception_type, exception_value, tb, request)
        )

    def check_error(self, data: dict, func: str = "") -> bool:
        """

        :param data:
        :param func:
        :return:

        """
        if data["status"] != "error":
            return False
        error_code = data['err-code']
        error_msg = data['err-msg']

        self.gateway.write_log(f"{func}请求出错，代码：{error_code},信息：{error_msg}")
        return True
