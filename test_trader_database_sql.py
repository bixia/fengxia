import unittest
from trader_database_sql import *
# TYPE_CHECKING = True

from trader_setting import SETTINGS


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        sqlite = Driver.SQLITE
        sqliteDriver = init(sqlite, SETTINGS)


    def test_something(self):

        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
