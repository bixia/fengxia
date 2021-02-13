import unittest

from trader_database_sql import *
from trader_setting import SETTINGS
from trader_constant import Exchange

# TYPE_CHECKING = True


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        sqlite = Driver.SQLITE
        self.sqliteDriver = init(sqlite, SETTINGS)

    def test_writeTick(self):
        tick: TickData = TickData(
            gateway_name="HUOBI",
            symbol="eth-usdt",
            exchange=Exchange.HUOBI,
            datetime=datetime.now(),
            name="eth-usdt",
            volume=1.0,
            open_interest=2,
            last_price=2,
            last_volume=2,
            limit_up=2,
            limit_down=2,

            open_price=2,
            high_price=2,
            low_price=2,
            pre_close=2,

            bid_price_1=2,
            bid_price_2=2,
            bid_price_3=2,
            bid_price_4=2,
            bid_price_5=2,

            ask_price_1=2,
            ask_price_2=2,
            ask_price_3=2,
            ask_price_4=2,
            ask_price_5=2,

            bid_volume_1=2,
            bid_volume_2=2,
            bid_volume_3=2,
            bid_volume_4=2,
            bid_volume_5=2,

            ask_volume_1=1.0,
            ask_volume_2=1.0,
            ask_volume_3=1.0,
            ask_volume_4=1.0,
            ask_volume_5=1.0,
        )
        print(tick.exchange.value)
        self.sqliteDriver.save_tick_data([tick])
        print(datetime(year=2019, month=10, day=10))
        print(datetime.now())
        # tick = self.sqliteDriver.load_tick_data(symbol='eth-usdt', exchange=Exchange.HUOBI,
        #                                         start=datetime(year=2019, month=10, day=10),
        #                                         end=datetime.now())
        # print(tick)


if __name__ == '__main__':
    unittest.main()
