import math
import unittest

from exotic_randoms import DoublePendulumConfig, DoublePendulumRandom


class DoublePendulumRandomTests(unittest.TestCase):
    def test_same_seed_reproduces_coordinate_sequence(self):
        left = DoublePendulumRandom(seed="chaos")
        right = DoublePendulumRandom(seed="chaos")

        self.assertEqual(
            [left.random() for _ in range(12)],
            [right.random() for _ in range(12)],
        )

    def test_coordinates_are_finite_and_bounded_by_total_length(self):
        config = DoublePendulumConfig(length1=1.5, length2=0.75)
        generator = DoublePendulumRandom(seed=7, config=config)
        limit = config.length1 + config.length2

        for _ in range(100):
            point = generator.next()
            self.assertEqual(len(point), 3)
            self.assertTrue(all(math.isfinite(value) for value in point))
            distance = math.sqrt(sum(value * value for value in point))
            self.assertLessEqual(distance, limit + 1e-12)

    def test_successive_outputs_advance_time_and_change(self):
        generator = DoublePendulumRandom(seed=3)

        first = generator.random()
        first_time = generator.metadata()["time"]
        second = generator.random()
        second_time = generator.metadata()["time"]

        self.assertNotEqual(first, second)
        self.assertAlmostEqual(
            first_time,
            generator.config.dt * generator.config.substeps,
        )
        self.assertAlmostEqual(
            second_time,
            first_time + generator.config.dt * generator.config.substeps,
        )

    def test_debug_exposes_simulation_state_without_raw_seed(self):
        generator = DoublePendulumRandom(seed="private")

        debug = generator.debug()

        self.assertIn("state", debug)
        self.assertIn("config", debug)
        self.assertIn("tip_position", debug)
        self.assertNotIn("private", repr(debug))

    def test_invalid_config_is_rejected(self):
        with self.assertRaises(ValueError):
            DoublePendulumConfig(dt=0.0)
        with self.assertRaises(ValueError):
            DoublePendulumConfig(substeps=0)
        with self.assertRaises(ValueError):
            DoublePendulumConfig(damping=-1.0)


if __name__ == "__main__":
    unittest.main()
