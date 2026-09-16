"""Common public API for the Exotic Random Generator Pack."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import Any

from entropy import Seed, SeedInfo, create_rng


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


__all__ = ["ExoticRandomBase", "ExoticRandomError", "Seed", "SeedInfo"]
