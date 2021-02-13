import unittest
from datetime import datetime

from trader_constant import Exchange
from trader_engine_omsengine import *


class Test2Engine(BaseEngine):
    def __init__(self):
        super(Test2Engine, self).__init__(main_engine=None, event_engine=None, engine_name="test2")


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.main_engine = Test2Engine()
        self.event_engine = EventEngine()
        self.oms_engine = OmsEngine(main_engine=self.main_engine, event_engine=self.event_engine)

        self.event_engine.start()

    def test_init(self):
        handlers = self.event_engine._handlers
        # print(handlers)
        # for k, v in handlers.items():
        #     print(f"{k}-{v}")
        self.assertEqual([EVENT_TICK, EVENT_ORDER, EVENT_TRADE, EVENT_POSITION, EVENT_ACCOUNT, EVENT_CONTRACT],
                         list(handlers.keys()))

    def test_tickevent(self):
        tickdata = TickData(gateway_name='lqw', symbol='LQW_USDT', exchange=Exchange.HUOBI, datetime=datetime.now())
        tickdata.datetime = ""
        event = Event(EVENT_TICK, tickdata)
        self.event_engine.put(event)
        q = self.event_engine._queue
        # while not q.empty():
        #     try:
        #         e: Event = q.get(block=True, timeout=1)
        #         print(e.type, e.data)
        #     except Empty:
        #         pass
        # self.event_engine._thread.join(timeout=2)
        self.event_engine._timer.join(timeout=1)
        expected = {'LQW_USDT.HUOBI': TickData(gateway_name='lqw', symbol='LQW_USDT',
                                               exchange=Exchange.HUOBI, datetime="", name='', volume=0, open_interest=0,
                                               last_price=0, last_volume=0, limit_up=0, limit_down=0, open_price=0,
                                               high_price=0, low_price=0, pre_close=0, bid_price_1=0, bid_price_2=0,
                                               bid_price_3=0, bid_price_4=0, bid_price_5=0, ask_price_1=0,
                                               ask_price_2=0, ask_price_3=0, ask_price_4=0, ask_price_5=0,
                                               bid_volume_1=0, bid_volume_2=0, bid_volume_3=0, bid_volume_4=0,
                                               bid_volume_5=0, ask_volume_1=0, ask_volume_2=0, ask_volume_3=0,
                                               ask_volume_4=0, ask_volume_5=0)}

        self.assertEqual(expected, self.oms_engine.ticks)

    def test_gettick(self):
        tickdata = TickData(gateway_name='GetTick', symbol='LQW_USDT', exchange=Exchange.HUOBI, datetime=datetime.now())
        tickdata.datetime = ""
        event = Event(EVENT_TICK, tickdata)
        self.event_engine.put(event)
        self.event_engine._timer.join(timeout=1)

        self.assertEqual(self.oms_engine.get_tick(tickdata.vt_symbol), tickdata)

    def tearDown(self) -> None:
        self.oms_engine.event_engine.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
