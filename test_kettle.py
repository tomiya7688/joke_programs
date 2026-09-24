import statistics
import unittest

from exotic_randoms import KettleConfig, KettleEvaporationRandom


class KettleEvaporationRandomTests(unittest.TestCase):
    def test_same_seed_reproduces_sequence(self):
        left = KettleEvaporationRandom(seed="same-kettle")
        right = KettleEvaporationRandom(seed="same-kettle")

        self.assertEqual(
            [left.random() for _ in range(5)],
            [right.random() for _ in range(5)],
        )

    def test_default_runs_finish_with_bounded_seconds(self):
        generator = KettleEvaporationRandom(seed="bounded")

        values = [generator.random() for _ in range(20)]

        self.assertTrue(all(isinstance(value, int) for value in values))
        self.assertTrue(all(1 <= value <= generator.config.max_seconds for value in values))
        self.assertGreater(len(set(values)), 1)
        self.assertGreater(statistics.mean(values), 300)

    def test_more_power_finishes_sooner_with_same_random_stream(self):
        slow = KettleEvaporationRandom(
            seed="power-comparison",
            config=KettleConfig(power_w=1000.0, max_seconds=2400),
        )
        fast = KettleEvaporationRandom(
            seed="power-comparison",
            config=KettleConfig(power_w=2000.0, max_seconds=2400),
        )

        self.assertGreater(slow.random(), fast.random())

    def test_timeout_is_bounded_and_visible_in_debug(self):
        generator = KettleEvaporationRandom(
            seed="timeout",
            config=KettleConfig(power_w=50.0, max_seconds=30),
        )

        with self.assertRaises(RuntimeError):
            generator.random()

        result = generator.debug()["last_result"]
        self.assertFalse(result["completed"])
        self.assertEqual(result["elapsed_seconds"], 30)
        self.assertGreater(result["final_volume_ml"], 0.0)

    def test_debug_reports_last_completed_run_without_raw_seed(self):
        generator = KettleEvaporationRandom(seed="private-kettle")
        seconds = generator.random()

        debug = generator.debug()

        self.assertTrue(debug["last_result"]["completed"])
        self.assertEqual(debug["last_result"]["elapsed_seconds"], seconds)
        self.assertEqual(debug["unit"], "seconds")
        self.assertNotIn("private-kettle", repr(debug))

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            KettleConfig(initial_volume_ml=0)
        with self.assertRaises(ValueError):
            KettleConfig(power_w=0)
        with self.assertRaises(ValueError):
            KettleConfig(airflow=-0.1)
        with self.assertRaises(ValueError):
            KettleConfig(initial_temp_c=101)
        with self.assertRaises(ValueError):
            KettleConfig(max_seconds=0)


if __name__ == "__main__":
    unittest.main()
