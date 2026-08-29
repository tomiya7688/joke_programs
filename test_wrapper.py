import unittest

from frog import FROG_VOICES
from wrapper import ExoticRandomWrapper, create_default_wrapper


class Counter:
    def __init__(self, start=0):
        self.value = start

    def next(self):
        self.value += 1
        return self.value


class CallableGenerator:
    def __call__(self, suffix=""):
        return f"generated:{suffix}"


class WrapperTests(unittest.TestCase):
    def test_register_create_and_auto_invoke_next(self):
        wrapper = ExoticRandomWrapper({"counter": Counter})

        wrapper.create("counter", start=4)

        self.assertEqual(wrapper.available(), ("counter",))
        self.assertEqual(wrapper.invoke("counter"), 5)

    def test_explicit_method_can_read_a_property_or_call_talk(self):
        wrapper = create_default_wrapper()
        wrapper.create("frog", position=(1.0, 1.0, 1.0), max_step=0.0)

        answer = wrapper.invoke("frog", method="talk", message="こんにちは")
        self.assertIn(answer, FROG_VOICES)
        self.assertIsInstance(answer, str)

    def test_invoke_all_and_callable_fallback(self):
        wrapper = ExoticRandomWrapper(
            {"counter": Counter, "callable": CallableGenerator}
        )
        wrapper.create("counter")
        wrapper.create("callable")

        self.assertEqual(
            wrapper.invoke_all({"callable": "__call__", "counter": "next"}),
            {"callable": "generated:", "counter": 1},
        )

    def test_duplicate_and_unknown_names_are_rejected(self):
        wrapper = ExoticRandomWrapper({"counter": Counter})

        with self.assertRaises(ValueError):
            wrapper.register("counter", Counter)
        with self.assertRaises(KeyError):
            wrapper.create("missing")
        with self.assertRaises(RuntimeError):
            wrapper.get("counter")


if __name__ == "__main__":
    unittest.main()
