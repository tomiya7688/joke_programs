import unittest

from entropy import create_rng, derive_seed_bytes, normalize_seed


class EntropyTests(unittest.TestCase):
    def test_same_seed_and_algorithm_reproduce_sequence(self):
        left, left_info = create_rng("same-seed", "demo")
        right, right_info = create_rng("same-seed", "demo")

        self.assertTrue(left_info.deterministic)
        self.assertEqual(left_info, right_info)
        self.assertEqual(
            [left.random() for _ in range(8)],
            [right.random() for _ in range(8)],
        )

    def test_algorithm_name_separates_streams(self):
        left, _ = create_rng("same-seed", "algorithm-a")
        right, _ = create_rng("same-seed", "algorithm-b")

        self.assertNotEqual(
            [left.random() for _ in range(8)],
            [right.random() for _ in range(8)],
        )

    def test_seed_types_are_separated(self):
        int_seed, _ = normalize_seed(1)
        str_seed, _ = normalize_seed("1")
        bytes_seed, _ = normalize_seed(b"1")

        self.assertEqual(len({int_seed, str_seed, bytes_seed}), 3)

    def test_none_seed_uses_nondeterministic_mode(self):
        _, first = create_rng(None, "demo")
        _, second = create_rng(None, "demo")

        self.assertFalse(first.deterministic)
        self.assertFalse(second.deterministic)
        self.assertNotEqual(first.seed_fingerprint, second.seed_fingerprint)

    def test_derive_seed_bytes_validates_arguments(self):
        material, _ = normalize_seed("seed")

        with self.assertRaises(ValueError):
            derive_seed_bytes(material, "")
        with self.assertRaises(ValueError):
            derive_seed_bytes(material, "demo", length=0)


if __name__ == "__main__":
    unittest.main()
