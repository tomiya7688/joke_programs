import unittest

from exotic_randoms import ExoticRandomBase


class DemoRandom(ExoticRandomBase):
    algorithm_name = "demo-random"

    def random(self):
        return self._rng.randrange(10_000)


class MissingNameRandom(ExoticRandomBase):
    def random(self):
        return 0


class ExoticRandomBaseTests(unittest.TestCase):
    def test_next_delegates_to_random_reproducibly(self):
        left = DemoRandom(seed="frog")
        right = DemoRandom(seed="frog")

        self.assertEqual(
            [left.next() for _ in range(5)],
            [right.random() for _ in range(5)],
        )

    def test_metadata_exposes_mode_without_raw_seed(self):
        generator = DemoRandom(seed="secret-ish")
        metadata = generator.metadata()

        self.assertEqual(metadata["algorithm_name"], "demo-random")
        self.assertTrue(metadata["deterministic"])
        self.assertEqual(len(metadata["seed_fingerprint"]), 16)
        self.assertNotIn("secret-ish", repr(metadata))
        self.assertEqual(generator.debug(), metadata)

    def test_missing_algorithm_name_is_rejected(self):
        with self.assertRaises(ValueError):
            MissingNameRandom(seed=1)


if __name__ == "__main__":
    unittest.main()
