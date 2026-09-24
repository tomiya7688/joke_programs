import statistics
import unittest

from exotic_randoms import BingoConfig, BingoWinnerTurnRandom


class BingoWinnerTurnRandomTests(unittest.TestCase):
    def test_same_seed_reproduces_turn_sequence(self):
        left = BingoWinnerTurnRandom(seed="same-bingo")
        right = BingoWinnerTurnRandom(seed="same-bingo")

        self.assertEqual(
            [left.random() for _ in range(20)],
            [right.random() for _ in range(20)],
        )

    def test_results_are_bounded_and_games_always_finish(self):
        generator = BingoWinnerTurnRandom(seed="bounded")

        results = [generator.random() for _ in range(100)]

        self.assertTrue(all(isinstance(turn, int) for turn in results))
        self.assertTrue(all(4 <= turn <= 75 for turn in results))

    def test_default_distribution_is_centered_in_the_midgame(self):
        generator = BingoWinnerTurnRandom(seed="distribution")

        results = [generator.random() for _ in range(300)]

        self.assertGreaterEqual(statistics.mean(results), 20.0)
        self.assertLessEqual(statistics.mean(results), 35.0)
        middle_fraction = sum(20 <= turn <= 40 for turn in results) / len(results)
        self.assertGreaterEqual(middle_fraction, 0.70)

    def test_debug_reports_last_game_without_raw_seed(self):
        generator = BingoWinnerTurnRandom(seed="private-seed")
        self.assertIsNone(generator.debug()["last_result"])

        turn = generator.random()
        debug = generator.debug()

        self.assertEqual(debug["last_result"]["winner_turn"], turn)
        self.assertGreaterEqual(len(debug["last_result"]["winning_players"]), 1)
        self.assertNotIn("private-seed", repr(debug))

    def test_config_validation(self):
        with self.assertRaises(ValueError):
            BingoConfig(player_count=0)
        with self.assertRaises(ValueError):
            BingoConfig(player_count=10_001)
        with self.assertRaises(TypeError):
            BingoConfig(free_center=1)
        with self.assertRaises(TypeError):
            BingoConfig(include_diagonals="yes")


if __name__ == "__main__":
    unittest.main()
