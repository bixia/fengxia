import unittest
from datetime import datetime

from trader_engine_email import *


class TestEngine(BaseEngine):
    def __init__(self):
        super(TestEngine, self).__init__(main_engine=None, event_engine=None, engine_name="test")


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.main_engine = TestEngine()
        self.email_engine = EmailEngine(main_engine=self.main_engine, event_engine=None)

    def test_sendemail(self) -> None:
        self.email_engine.send_email(subject="hello", content="from vnpy", receiver="343224563@qq.com")

    def test_mainengine(self) -> None:
        self.main_engine.send_email(subject="Main_engine", content=f"{datetime.now().strftime('%Y%m%d')}")

    def tearDown(self) -> None:
        self.email_engine.close()


if __name__ == '__main__':
    unittest.main()
