from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence, List, Dict, TYPE_CHECKING

from pytz import timezone

from trader_setting import SETTINGS

if not TYPE_CHECKING:
    from trader_constant import Interval, Exchange
    from trader_object import BarData, TickData

DB_TZ = timezone(SETTINGS["database.timezone"])


class Driver(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    INFLUX = "influxdb"


class BaseDatabaseManager(ABC):

    @abstractmethod
    def load_bar_data(self,
                      symbol: str,
                      exchange: Exchange,
                      interval: Interval,
                      start: datetime,
                      end: datetime
                      ) -> Sequence["BarData"]:
        pass

    @abstractmethod
    def load_tick_data(self,
                       symbol: str,
                       exchange: Exchange,
                       start: datetime,
                       end: datetime
                       ) -> Sequence["TickData"]:
        pass

    @abstractmethod
    def save_bar_data(self,
                      datas: Sequence["BarData"]
                      ) -> None:
        pass

    @abstractmethod
    def save_tick_data(self,
                       data: Sequence["TickData"]
                       ) -> None:
        pass

    @abstractmethod
    def get_newest_bar_data(self,
                            symbol: str,
                            exchange: Exchange,
                            interval: Interval
                            ) -> Optional[BarData]:
        """
        if there is data in database, return the one with greatest datetime(newest one)
        :param symbol:
        :param exchange:
        :param interval:
        :return:
        """
        pass

    @abstractmethod
    def get_oldest_bar_data(self,
                            symbol: str,
                            exchange: Exchange,
                            interval: Interval,
                            ) -> Optional[BarData]:
        """
        if there is data in database, return the one with smallest datetime(oldest one)
        :param symbol:
        :param exchange:
        :param interval:
        :return:
        """
        pass

    @abstractmethod
    def get_newest_tick_data(self,
                             symbol: str,
                             exchange: Exchange
                             ) -> Optional[TickData]:
        pass

    @abstractmethod
    def get_bar_data_statistics(self,
                                symbol: str,
                                exchange: Exchange
                                ) -> List[Dict]:
        """
        return data avaiable in database with a list of symbol/exchange/interval/count
        :param symbol:
        :param exchange:
        :return:
        """
        pass

    @abstractmethod
    def delete_bar_data(self,
                        symbol: str,
                        exchange: Exchange,
                        interval: Interval
                        ) -> int:
        """
        delete all bar data with given symbol + exchange + interval
        :param symbol:
        :param exchange:
        :param interval:
        :return:
        """
        pass

    @abstractmethod
    def clean(self,
              symbol: str):
        """
        delete all records for a symbol
        :param symbol:
        :return:
        """
        pass
