"""Bounded kettle heating and evaporation simulation."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random


@dataclass(frozen=True, slots=True)
class KettleConfig:
    """Physical-ish inputs for one kettle evaporation run."""

    initial_volume_ml: float = 250.0
    initial_temp_c: float = 20.0
    power_w: float = 1500.0
    room_temp_c: float = 20.0
    airflow: float = 0.35
    heat_loss_w_per_c: float = 2.5
    step_seconds: float = 1.0
    max_seconds: int = 1800

    def __post_init__(self) -> None:
        finite_positive = (
            ("initial_volume_ml", self.initial_volume_ml),
            ("power_w", self.power_w),
            ("step_seconds", self.step_seconds),
        )
        for name, value in finite_positive:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a number")
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")

        finite_values = (
            ("initial_temp_c", self.initial_temp_c),
            ("room_temp_c", self.room_temp_c),
            ("airflow", self.airflow),
            ("heat_loss_w_per_c", self.heat_loss_w_per_c),
        )
        for name, value in finite_values:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a number")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

        if self.airflow < 0:
            raise ValueError("airflow must be non-negative")
        if self.heat_loss_w_per_c < 0:
            raise ValueError("heat_loss_w_per_c must be non-negative")
        if not -50.0 <= self.initial_temp_c <= 100.0:
            raise ValueError("initial_temp_c must be between -50 and 100 C")
        if not isinstance(self.max_seconds, int) or isinstance(self.max_seconds, bool):
            raise TypeError("max_seconds must be an integer")
        if self.max_seconds <= 0:
            raise ValueError("max_seconds must be positive")


@dataclass(frozen=True, slots=True)
class KettleResult:
    """Outcome of one bounded evaporation run."""

    elapsed_seconds: int
    completed: bool
    final_volume_ml: float
    final_temp_c: float
    peak_temp_c: float
    effective_efficiency: float
    effective_airflow: float


class KettleSimulation:
    """Advance water temperature and mass in fixed timesteps."""

    WATER_DENSITY_G_PER_ML = 0.997
    SPECIFIC_HEAT_J_PER_G_C = 4.186
    LATENT_HEAT_J_PER_G = 2256.0
    BOILING_TEMP_C = 100.0

    def __init__(self, rng: random.Random, config: KettleConfig | None = None) -> None:
        self._rng = rng
        self.config = config if config is not None else KettleConfig()
        self.last_result: KettleResult | None = None

    def run(self) -> KettleResult:
        """Simulate a fresh kettle until dry or the configured time limit."""

        config = self.config
        mass_g = config.initial_volume_ml * self.WATER_DENSITY_G_PER_ML
        temp_c = float(config.initial_temp_c)
        peak_temp_c = temp_c
        elapsed = 0.0

        # These run-level factors make each kettle have a persistent character.
        effective_efficiency = self._rng.uniform(0.78, 0.98)
        effective_airflow = max(0.0, config.airflow * self._rng.uniform(0.55, 1.65))

        while mass_g > 1e-9 and elapsed < config.max_seconds:
            dt = min(config.step_seconds, config.max_seconds - elapsed)

            flame_factor = self._rng.uniform(0.90, 1.10)
            gust = max(
                0.0,
                effective_airflow * (1.0 + self._rng.uniform(-0.35, 0.35)),
            )
            heat_loss_w = (
                config.heat_loss_w_per_c
                * max(temp_c - config.room_temp_c, 0.0)
                * (1.0 + 0.50 * gust)
            )
            useful_energy_j = max(
                0.0,
                config.power_w * effective_efficiency * flame_factor - heat_loss_w,
            ) * dt

            if temp_c < self.BOILING_TEMP_C:
                energy_to_boil_j = (
                    mass_g
                    * self.SPECIFIC_HEAT_J_PER_G_C
                    * (self.BOILING_TEMP_C - temp_c)
                )
                if useful_energy_j < energy_to_boil_j:
                    temp_c += useful_energy_j / (
                        mass_g * self.SPECIFIC_HEAT_J_PER_G_C
                    )
                    useful_energy_j = 0.0
                else:
                    temp_c = self.BOILING_TEMP_C
                    useful_energy_j -= energy_to_boil_j

            if temp_c >= self.BOILING_TEMP_C:
                evaporated_by_heat_g = useful_energy_j / self.LATENT_HEAT_J_PER_G
                evaporated_by_airflow_g = 0.005 * gust * dt
                mass_g = max(
                    0.0,
                    mass_g - evaporated_by_heat_g - evaporated_by_airflow_g,
                )

            elapsed += dt
            peak_temp_c = max(peak_temp_c, temp_c)

        completed = mass_g <= 1e-9
        result = KettleResult(
            elapsed_seconds=math.ceil(elapsed),
            completed=completed,
            final_volume_ml=max(0.0, mass_g / self.WATER_DENSITY_G_PER_ML),
            final_temp_c=temp_c,
            peak_temp_c=peak_temp_c,
            effective_efficiency=effective_efficiency,
            effective_airflow=effective_airflow,
        )
        self.last_result = result
        return result


__all__ = ["KettleConfig", "KettleResult", "KettleSimulation"]
