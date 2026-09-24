"""Standard 75-ball bingo simulation used by BingoWinnerTurnRandom."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import TypeAlias


BingoCell: TypeAlias = int | None
BingoCard: TypeAlias = tuple[
    tuple[BingoCell, BingoCell, BingoCell, BingoCell, BingoCell],
    tuple[BingoCell, BingoCell, BingoCell, BingoCell, BingoCell],
    tuple[BingoCell, BingoCell, BingoCell, BingoCell, BingoCell],
    tuple[BingoCell, BingoCell, BingoCell, BingoCell, BingoCell],
    tuple[BingoCell, BingoCell, BingoCell, BingoCell, BingoCell],
]


@dataclass(frozen=True, slots=True)
class BingoConfig:
    """Configuration for one standard 75-ball bingo game."""

    player_count: int = 8
    free_center: bool = True
    include_diagonals: bool = True

    def __post_init__(self) -> None:
        if (
            not isinstance(self.player_count, int)
            or isinstance(self.player_count, bool)
            or self.player_count <= 0
        ):
            raise ValueError("player_count must be a positive integer")
        if self.player_count > 10_000:
            raise ValueError("player_count must be at most 10000")
        if not isinstance(self.free_center, bool):
            raise TypeError("free_center must be bool")
        if not isinstance(self.include_diagonals, bool):
            raise TypeError("include_diagonals must be bool")


@dataclass(frozen=True, slots=True)
class BingoGameResult:
    """Result of one completed bingo game."""

    winner_turn: int
    last_number: int
    winning_players: tuple[int, ...]


class BingoSimulation:
    """Generate cards, draw balls, and stop at the first winning turn."""

    BALL_COUNT = 75
    CARD_SIZE = 5
    COLUMN_RANGES = (
        range(1, 16),
        range(16, 31),
        range(31, 46),
        range(46, 61),
        range(61, 76),
    )

    def __init__(self, rng: random.Random, config: BingoConfig | None = None) -> None:
        self._rng = rng
        self.config = config if config is not None else BingoConfig()
        self.last_result: BingoGameResult | None = None

    def play(self) -> BingoGameResult:
        """Play one complete game and return the first winning turn."""

        cards = tuple(self._create_card() for _ in range(self.config.player_count))
        draw_order = list(range(1, self.BALL_COUNT + 1))
        self._rng.shuffle(draw_order)
        drawn: set[int] = set()

        for turn, number in enumerate(draw_order, start=1):
            drawn.add(number)
            winners = tuple(
                index
                for index, card in enumerate(cards)
                if self._has_bingo(card, drawn)
            )
            if winners:
                result = BingoGameResult(
                    winner_turn=turn,
                    last_number=number,
                    winning_players=winners,
                )
                self.last_result = result
                return result

        raise RuntimeError("a 75-ball bingo game ended without a winner")

    def _create_card(self) -> BingoCard:
        rows: list[list[BingoCell]] = [[None] * self.CARD_SIZE for _ in range(self.CARD_SIZE)]
        for column, number_range in enumerate(self.COLUMN_RANGES):
            values = self._rng.sample(tuple(number_range), self.CARD_SIZE)
            for row, value in enumerate(values):
                rows[row][column] = value

        if self.config.free_center:
            rows[2][2] = None

        return tuple(tuple(row) for row in rows)  # type: ignore[return-value]

    def _has_bingo(self, card: BingoCard, drawn: set[int]) -> bool:
        lines: list[tuple[BingoCell, ...]] = list(card)
        lines.extend(
            tuple(card[row][column] for row in range(self.CARD_SIZE))
            for column in range(self.CARD_SIZE)
        )
        if self.config.include_diagonals:
            lines.append(tuple(card[i][i] for i in range(self.CARD_SIZE)))
            lines.append(tuple(card[i][self.CARD_SIZE - 1 - i] for i in range(self.CARD_SIZE)))

        return any(
            all(cell is None or cell in drawn for cell in line)
            for line in lines
        )


__all__ = ["BingoCard", "BingoConfig", "BingoGameResult", "BingoSimulation"]
