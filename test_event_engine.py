# -*- coding: utf-8 -*-

import unittest

from event_engine import *


class TestEngine(unittest.TestCase):

    def test_fuc1(self):
        self.assertEqual(1, 1)

    def test_register(self):
        engine = EventEngine()
        handler = None
        engine.register("1st", handler)
        expected = {"1st": [handler]}
        self.assertEqual(expected, engine._handlers)
        print(engine._handlers)

    def test_unregister(self):
        engine = EventEngine(1)
        handler = None
        engine.register("1st", handler)
        expected = {"1st": [handler]}
        print(engine._handlers)
        self.assertEqual(expected, engine._handlers)
        engine.unregister("1st", handler)
        expected = {}
        print(engine._handlers)
        self.assertEqual(expected, engine._handlers)

    def test_put(self):
        engine = EventEngine()
        event = Event("Type", {1: [1, 2]})
        engine.put(event)
        while not engine._queue.empty():
            try:
                e = engine._queue.get()
                m = f"{e.type}--{e.data}"
                self.assertEqual("Type--{1: [1, 2]}", m)
            except Empty:
                pass

    def call(self, event: Event) -> str:
        m = f"{event.type}-{event.data}"
        print("/n")
        print(m)
        return m

    def call2(self, event: Event) -> str:
        m = f"{event.type}+{event.data}"
        print("/n")
        print(m)
        return m

    def test_start(self):
        engine = EventEngine()
        event = Event("Test", [1, 2, 3])
        engine.put(event)
        event2 = Event("Test2", ['aaaa'])
        engine.put(event2)

        engine.register("Test", self.call)
        engine.register("Test2", self.call2)
        engine.start()
        print(engine._thread.is_alive())
        print(engine._timer.is_alive())
        engine.stop()
        print(engine._thread.is_alive())
        print(engine._timer.is_alive())


if __name__ == '__main__':
    unittest.main(verbosity=2)
