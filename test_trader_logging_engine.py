from trader_logging_engine import *
from event_engine import *
from trader_object import LogData
import unittest
from io import StringIO
from unittest.mock import patch


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.event_engine = EventEngine()
        self.event_engine.start()

        self.logger_engine = LogEngine(None, self.event_engine)

    def test_writelog(self):
        logdata = LogData(msg={1: 'a'}, gateway_name='lqw')
        print(logdata)
        event = Event(EVENT_LOG, logdata)
        self.event_engine.put(event)
        # self.assertEqual()

    def tearDown(self) -> None:
        self.event_engine.stop()
        self.logger_engine.close()


if __name__ == '__main__':
    unittest.main()
