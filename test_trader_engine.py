import unittest
from trader_engine import *


class TestMainEngine(unittest.TestCase):

    def testInit(self):
        main_engine = MainEngine()
        print(main_engine)


if __name__ == "__main__":
    unittest.main()
