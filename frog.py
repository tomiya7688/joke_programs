"""A small, bounded three-dimensional frog model."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import math
import random
import time


AxisRange = tuple[float, float]
Position3D = tuple[float, float, float]
FROG_VOICES = (
    "ゲコッ",
    "ゲコゲコ",
    "ケロッ",
    "ケロケロ",
    "クワッ",
    "クワクワ",
    "グワッ",
    "グワグワ",
    "ゲロッ",
    "ゲロゲロ",
    "コロッ",
    "コロコロ",
    "クックッ",
    "ケケッ",
    "ギャッ",
    "グェッ",
    "ポコッ",
    "キュッ",
    "ケロロン",
    "ゲコロン",
)


@dataclass(frozen=True, slots=True)
class Bounds3D:
    """Inclusive coordinate limits for each axis."""

    x: AxisRange = (0.0, 100.0)
    y: AxisRange = (0.0, 100.0)
    z: AxisRange = (0.0, 100.0)

    def __post_init__(self) -> None:
        for axis_name, axis_range in (("x", self.x), ("y", self.y), ("z", self.z)):
            if len(axis_range) != 2:
                raise ValueError(f"{axis_name} range must contain exactly two values")

            lower, upper = axis_range
            if not (math.isfinite(lower) and math.isfinite(upper)):
                raise ValueError(f"{axis_name} range values must be finite")
            if lower > upper:
                raise ValueError(f"{axis_name} range must be ordered low to high")

    def contains(self, position: Position3D) -> bool:
        """Return whether position lies inside all three ranges."""

        return all(
            lower <= coordinate <= upper
            for coordinate, (lower, upper) in zip(
                position, (self.x, self.y, self.z), strict=True
            )
        )

    def clamp(self, position: Position3D) -> Position3D:
        """Clamp position to the nearest point inside these bounds."""

        return tuple(
            min(max(coordinate, lower), upper)
            for coordinate, (lower, upper) in zip(
                position, (self.x, self.y, self.z), strict=True
            )
        )  # type: ignore[return-value]


class Frog:
    """A frog which moves inside a bounded three-dimensional space.

    If no initial position is supplied, one is selected randomly from the
    configured bounds. Reading x, y, z or position advances a two-part hop:
    first the frog leaps forward and upward, then it lands while continuing in
    the same horizontal direction. The movement itself is private, so a caller
    cannot command the frog to move.

    Age is measured in seconds using a monotonic clock, so wall-clock
    adjustments do not make the frog younger or older unexpectedly.
    """

    def __init__(
        self,
        *,
        bounds: Bounds3D | None = None,
        position: Position3D | None = None,
        max_step: float = 1.0,
        voices: Sequence[str] | None = None,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.bounds = bounds if bounds is not None else Bounds3D()

        if not math.isfinite(max_step) or max_step < 0:
            raise ValueError("max_step must be a finite, non-negative number")
        self.max_step = float(max_step)

        voice_options = FROG_VOICES if voices is None else tuple(voices)
        if (
            isinstance(voices, str)
            or not voice_options
            or any(not isinstance(voice, str) or not voice for voice in voice_options)
        ):
            raise ValueError("voices must contain one or more non-empty strings")
        self.voices = voice_options

        self._rng = rng if rng is not None else random.Random()
        self._clock = clock
        self._born_at = self._clock()

        if position is None:
            initial_position: Position3D = (
                self._rng.uniform(*self.bounds.x),
                self._rng.uniform(*self.bounds.y),
                self._rng.uniform(*self.bounds.z),
            )
        else:
            initial_position = self._validate_position(position)
            if not self.bounds.contains(initial_position):
                raise ValueError("position must be inside bounds")

        self._x, self._y, self._z = initial_position
        self._airborne = False
        self._ground_z = self._z
        self._hop_dx = 0.0
        self._hop_dy = 0.0

    @property
    def x(self) -> float:
        """Move once and return the new x coordinate."""

        self._move()
        return self._x

    @property
    def y(self) -> float:
        """Move once and return the new y coordinate."""

        self._move()
        return self._y

    @property
    def z(self) -> float:
        """Move once and return the new z coordinate."""

        self._move()
        return self._z

    @property
    def position(self) -> Position3D:
        """Move once and return the new (x, y, z) coordinates."""

        return self._move()

    @property
    def age(self) -> float:
        """Seconds elapsed since this frog was created."""

        return max(0.0, self._clock() - self._born_at)

    def talk(self, message: str | None = None) -> str:
        """Talk to the frog and receive its voice as a string.

        The words do not control the frog's response. It moves on its own and
        randomly returns one of its configured voices.
        """

        if message is not None and not isinstance(message, str):
            raise TypeError("message must be a string or None")
        self._move()
        return self._rng.choice(self.voices)

    def _move(self) -> Position3D:
        """Advance one half of a frog-like hop and return the new position."""

        if self._airborne:
            next_position = (
                self._x + self._hop_dx,
                self._y + self._hop_dy,
                self._ground_z,
            )
            self._airborne = False
        else:
            angle = self._rng.uniform(0.0, math.tau)
            distance = self._rng.uniform(self.max_step * 0.5, self.max_step)
            jump_height = self._rng.uniform(self.max_step * 0.25, self.max_step * 0.75)

            self._hop_dx = math.cos(angle) * distance / 2.0
            self._hop_dy = math.sin(angle) * distance / 2.0
            self._ground_z = self._z
            next_position = (
                self._x + self._hop_dx,
                self._y + self._hop_dy,
                self._z + jump_height,
            )
            self._airborne = True

        self._x, self._y, self._z = self.bounds.clamp(next_position)
        return self._x, self._y, self._z

    @staticmethod
    def _validate_position(position: Position3D) -> Position3D:
        try:
            coordinates = tuple(float(value) for value in position)
        except (TypeError, ValueError) as error:
            raise ValueError("position must contain three finite numbers") from error

        if len(coordinates) != 3 or not all(math.isfinite(value) for value in coordinates):
            raise ValueError("position must contain three finite numbers")
        return coordinates  # type: ignore[return-value]

    def __repr__(self) -> str:
        return (
            f"Frog(x={self._x:.3f}, y={self._y:.3f}, z={self._z:.3f}, "
            f"age={self.age:.3f})"
        )


__all__ = ["Bounds3D", "FROG_VOICES", "Frog", "Position3D"]
