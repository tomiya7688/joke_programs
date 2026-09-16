"""Numerical double-pendulum simulation used by DoublePendulumRandom."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import TypeAlias


Position3D: TypeAlias = tuple[float, float, float]
State: TypeAlias = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class DoublePendulumConfig:
    """Physical and integration parameters for the double pendulum."""

    length1: float = 1.0
    length2: float = 1.0
    mass1: float = 1.0
    mass2: float = 1.0
    gravity: float = 9.81
    damping: float = 0.002
    drive_amplitude: float = 0.0
    drive_frequency: float = 1.0
    dt: float = 0.01
    substeps: int = 8

    def __post_init__(self) -> None:
        for name, value in {
            "length1": self.length1,
            "length2": self.length2,
            "mass1": self.mass1,
            "mass2": self.mass2,
            "gravity": self.gravity,
            "dt": self.dt,
        }.items():
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a finite positive number")

        for name, value in {
            "damping": self.damping,
            "drive_amplitude": self.drive_amplitude,
            "drive_frequency": self.drive_frequency,
        }.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

        if self.damping < 0:
            raise ValueError("damping must be non-negative")
        if (
            not isinstance(self.substeps, int)
            or isinstance(self.substeps, bool)
            or self.substeps <= 0
        ):
            raise ValueError("substeps must be a positive integer")


class DoublePendulumSimulation:
    """Classic planar double pendulum embedded in a seeded 3D vertical plane."""

    def __init__(self, rng: random.Random, config: DoublePendulumConfig) -> None:
        self.config = config
        self.time = 0.0

        # The physics stays the standard planar double-pendulum problem. The
        # plane itself is rotated around the vertical axis so the public output
        # is a genuine 3D coordinate while retaining the familiar equations.
        self.plane_azimuth = rng.uniform(0.0, math.tau)
        self.theta1 = rng.uniform(0.55 * math.pi, 0.95 * math.pi)
        self.theta2 = rng.uniform(0.55 * math.pi, 0.95 * math.pi)
        self.omega1 = rng.uniform(-0.15, 0.15)
        self.omega2 = rng.uniform(-0.15, 0.15)

    @property
    def state(self) -> State:
        """Return angles and angular velocities for both links."""

        return self.theta1, self.omega1, self.theta2, self.omega2

    def step(self) -> Position3D:
        """Advance the simulation and return the second bob position."""

        for _ in range(self.config.substeps):
            self._rk4_step()
        return self.tip_position()

    def tip_position(self) -> Position3D:
        """Return the second bob coordinate relative to the fixed pivot."""

        config = self.config
        radial = (
            config.length1 * math.sin(self.theta1)
            + config.length2 * math.sin(self.theta2)
        )
        z = -(
            config.length1 * math.cos(self.theta1)
            + config.length2 * math.cos(self.theta2)
        )
        return (
            radial * math.cos(self.plane_azimuth),
            radial * math.sin(self.plane_azimuth),
            z,
        )

    def _derivatives(self, state: State, time: float) -> State:
        theta1, omega1, theta2, omega2 = state
        config = self.config
        delta = theta1 - theta2
        cos_delta = math.cos(delta)
        sin_delta = math.sin(delta)
        common = (
            2.0 * config.mass1
            + config.mass2
            - config.mass2 * math.cos(2.0 * delta)
        )

        alpha1 = (
            -config.gravity
            * (2.0 * config.mass1 + config.mass2)
            * math.sin(theta1)
            - config.mass2
            * config.gravity
            * math.sin(theta1 - 2.0 * theta2)
            - 2.0
            * sin_delta
            * config.mass2
            * (
                omega2 * omega2 * config.length2
                + omega1 * omega1 * config.length1 * cos_delta
            )
        ) / (config.length1 * common)

        alpha2 = (
            2.0
            * sin_delta
            * (
                omega1
                * omega1
                * config.length1
                * (config.mass1 + config.mass2)
                + config.gravity
                * (config.mass1 + config.mass2)
                * math.cos(theta1)
                + omega2
                * omega2
                * config.length2
                * config.mass2
                * cos_delta
            )
        ) / (config.length2 * common)

        alpha1 += config.drive_amplitude * math.sin(config.drive_frequency * time)
        alpha1 -= config.damping * omega1
        alpha2 -= config.damping * omega2
        return omega1, alpha1, omega2, alpha2

    @staticmethod
    def _combine(state: State, derivative: State, scale: float) -> State:
        return tuple(
            value + scale * slope
            for value, slope in zip(state, derivative, strict=True)
        )  # type: ignore[return-value]

    def _rk4_step(self) -> None:
        dt = self.config.dt
        state = self.state
        k1 = self._derivatives(state, self.time)
        k2 = self._derivatives(
            self._combine(state, k1, dt / 2.0), self.time + dt / 2.0
        )
        k3 = self._derivatives(
            self._combine(state, k2, dt / 2.0), self.time + dt / 2.0
        )
        k4 = self._derivatives(self._combine(state, k3, dt), self.time + dt)

        next_state = tuple(
            value + (dt / 6.0) * (d1 + 2.0 * d2 + 2.0 * d3 + d4)
            for value, d1, d2, d3, d4 in zip(
                state, k1, k2, k3, k4, strict=True
            )
        )
        if not all(math.isfinite(value) for value in next_state):
            raise FloatingPointError("double-pendulum integration became non-finite")

        self.theta1 = math.remainder(next_state[0], math.tau)
        self.omega1 = next_state[1]
        self.theta2 = math.remainder(next_state[2], math.tau)
        self.omega2 = next_state[3]
        self.time += dt


__all__ = [
    "DoublePendulumConfig",
    "DoublePendulumSimulation",
    "Position3D",
    "State",
]
