import unittest
from typing import Dict

from event_engine import EventEngine
from gateway_1token_rest_client import *
from trader_logging_engine import LogEngine
from trader_object import SubscribeRequest


class TestGateway(BaseGateway):
    """
    test gateway for test
    """
    default_setting = {}
    exchanges = []

    def __init__(self):
        event_engine = EventEngine()
        super(TestGateway, self).__init__(event_engine, gateway_name="test")
        self.log_engine = LogEngine(None,event_engine)
        event_engine.start()

    def cancel_order(self, req: CancelRequest) -> None:
        pass

    def close(self) -> None:
        pass

    def connect(self, setting: Dict) -> None:
        pass

    def query_position(self) -> None:
        pass

    def query_account(self) -> None:
        pass

    def send_order(self, req: OrderRequest) -> str:
        pass

    def subscribe(self, req: SubscribeRequest) -> None:
        pass


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        test_gateway = TestGateway()
        self.one_token = OnetokenRestApi(test_gateway)

    def test_connect(self):
        self.one_token.connect(key="671nEF4o-8sdHwnwO-FjY4wT7u-A4c5ER3V",
                               secret="0D3GiA1J-HM47dnQT-fQzoaeey-IiFntaLA",
                               session_number=3,
                               exchange="huobi",
                               account="bixia1994",
                               proxy_port=0,
                               proxy_host="")

    def tearDown(self) -> None:
        self.one_token.gateway.close()
        self.one_token.gateway.event_engine.stop()
        self.one_token.join()
        self.one_token.stop()


if __name__ == '__main__':
    unittest.main()
