"""Common public API for the Exotic Random Generator Pack."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any

from entropy import Seed, SeedInfo, create_rng
from simulations.double_pendulum import (
    DoublePendulumConfig,
    DoublePendulumSimulation,
    Position3D,
)


class ExoticRandomError(Exception):
    """Base exception for exotic-random generator failures."""


class ExoticRandomBase(ABC):
    """Base class for reproducible, algorithm-separated generators.

    Subclasses provide a non-empty ``algorithm_name`` and implement
    :meth:`random`. ``next()`` is a common alias used by the wrapper API.
    """

    algorithm_name = ""

    def __init__(self, *, seed: Seed = None) -> None:
        if not isinstance(self.algorithm_name, str) or not self.algorithm_name.strip():
            raise ValueError("subclasses must define a non-empty algorithm_name")
        self._rng, self._seed_info = create_rng(seed, self.algorithm_name)

    @abstractmethod
    def random(self) -> Any:
        """Return one generated value."""

    def next(self) -> Any:
        """Return one generated value using the common wrapper-friendly name."""

        return self.random()

    def metadata(self) -> dict[str, Any]:
        """Return stable public metadata for the current generator."""

        return asdict(self._seed_info)

    def debug(self) -> dict[str, Any]:
        """Return generation metadata suitable for diagnostics."""

        return self.metadata()

    @property
    def seed_info(self) -> SeedInfo:
        """Return immutable seed metadata."""

        return self._seed_info


class DoublePendulumRandom(ExoticRandomBase):
    """Return successive 3D tip coordinates from a chaotic double pendulum.

    The underlying physics is the standard planar double-pendulum model. Its
    vertical plane is rotated around the z-axis by a seed-derived azimuth, so
    every result is a pivot-centered ``(x, y, z)`` coordinate in length units.
    Successive calls are intentionally time-correlated rather than independent.
    """

    algorithm_name = "double-pendulum"

    def __init__(
        self,
        *,
        seed: Seed = None,
        config: DoublePendulumConfig | None = None,
    ) -> None:
        super().__init__(seed=seed)
        self.config = config if config is not None else DoublePendulumConfig()
        self._simulation = DoublePendulumSimulation(self._rng, self.config)

    def random(self) -> Position3D:
        """Advance the pendulum and return its second bob coordinate."""

        return self._simulation.step()

    def metadata(self) -> dict[str, Any]:
        """Return seed metadata plus stable output semantics and time."""

        metadata = super().metadata()
        metadata.update(
            {
                "unit": "length-units",
                "coordinate_system": "pivot-centered 3D",
                "time": self._simulation.time,
            }
        )
        return metadata

    def debug(self) -> dict[str, Any]:
        """Return current simulation state and configuration for inspection."""

        debug = self.metadata()
        debug.update(
            {
                "state": self._simulation.state,
                "plane_azimuth": self._simulation.plane_azimuth,
                "config": asdict(self.config),
                "tip_position": self._simulation.tip_position(),
            }
        )
        return debug


__all__ = [
    "DoublePendulumConfig",
    "DoublePendulumRandom",
    "ExoticRandomBase",
    "ExoticRandomError",
    "Seed",
    "SeedInfo",
]
