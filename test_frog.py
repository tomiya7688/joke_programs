import math
import unittest

from frog import Bounds3D, FROG_VOICES, Frog


class SequenceRandom:
    def __init__(self, values, choices=()):
        self._values = iter(values)
        self._choices = iter(choices)
        self.calls = 0
        self.choice_calls = 0

    def uniform(self, lower, upper):
        self.calls += 1
        value = next(self._values)
        if not lower <= value <= upper:
            raise AssertionError(f"{value} is outside [{lower}, {upper}]")
        return value

    def choice(self, options):
        self.choice_calls += 1
        value = next(self._choices)
        if value not in options:
            raise AssertionError(f"{value!r} is not an available choice")
        return value


class ManualClock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


class FrogTests(unittest.TestCase):
    def test_random_initial_position_is_inside_bounds(self):
        bounds = Bounds3D(x=(-1.0, 1.0), y=(10.0, 20.0), z=(3.0, 4.0))
        frog = Frog(
            bounds=bounds,
            max_step=0.0,
            rng=SequenceRandom((0.5, 12.0, 3.75, 0.0, 0.0, 0.0)),
        )

        self.assertEqual(frog.position, (0.5, 12.0, 3.75))

    def test_reading_position_moves_and_clamps_to_bounds(self):
        frog = Frog(
            bounds=Bounds3D(x=(0.0, 1.0), y=(0.0, 1.0), z=(0.0, 1.0)),
            position=(0.9, 0.1, 0.5),
            max_step=1.0,
            rng=SequenceRandom((0.0, 1.0, 0.5)),
        )

        self.assertEqual(frog.position, (1.0, 0.1, 1.0))

    def test_reading_each_coordinate_moves_once(self):
        frog = Frog(
            bounds=Bounds3D(x=(0.0, 3.0), y=(0.0, 3.0), z=(0.0, 3.0)),
            position=(1.0, 1.0, 1.0),
            max_step=1.0,
            rng=SequenceRandom(
                (0.0, 1.0, 0.5, math.pi / 2.0, 1.0, 0.5)
            ),
        )

        self.assertEqual(frog.x, 1.5)
        self.assertEqual(frog.y, 1.0)
        self.assertEqual(frog._x, 2.0)
        self.assertEqual(frog.z, 1.5)

    def test_talk_moves_and_returns_the_frogs_voice(self):
        rng = SequenceRandom((0.0, 1.0, 0.5), choices=("ケロケロ",))
        frog = Frog(
            position=(1.0, 1.0, 1.0),
            max_step=1.0,
            rng=rng,
        )

        answer = frog.talk("こんにちは")

        self.assertEqual(answer, "ケロケロ")
        self.assertIsInstance(answer, str)
        self.assertEqual(rng.calls, 3)
        self.assertEqual(rng.choice_calls, 1)

    def test_twenty_default_voices_are_available(self):
        self.assertEqual(len(FROG_VOICES), 20)
        self.assertEqual(len(set(FROG_VOICES)), 20)
        self.assertTrue(all(isinstance(voice, str) and voice for voice in FROG_VOICES))

    def test_age_is_elapsed_time_since_creation(self):
        clock = ManualClock(100.0)
        frog = Frog(position=(1.0, 2.0, 3.0), clock=clock)

        self.assertEqual(frog.age, 0.0)
        clock.now = 102.5
        self.assertEqual(frog.age, 2.5)

    def test_position_outside_bounds_is_rejected(self):
        with self.assertRaises(ValueError):
            Frog(position=(101.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
