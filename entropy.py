"""Seed handling and algorithm-separated pseudo-random streams."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
import secrets
from typing import TypeAlias


Seed: TypeAlias = int | str | bytes | bytearray | memoryview | None
_DOMAIN = b"joke_programs.exotic_randoms.v1\0"


@dataclass(frozen=True, slots=True)
class SeedInfo:
    """Public metadata about a generator's seed mode.

    ``seed_fingerprint`` identifies the normalized seed material without
    exposing it. It is intended for debugging, not for security decisions.
    """

    algorithm_name: str
    deterministic: bool
    seed_fingerprint: str


def _validate_algorithm_name(algorithm_name: str) -> str:
    if not isinstance(algorithm_name, str) or not algorithm_name.strip():
        raise ValueError("algorithm_name must be a non-empty string")
    return algorithm_name


def normalize_seed(seed: Seed) -> tuple[bytes, bool]:
    """Return tagged seed bytes and whether the seed was user supplied.

    Different input types are deliberately domain-separated, so ``1``,
    ``"1"``, and ``b"1"`` do not produce the same stream.
    """

    if seed is None:
        return b"os\0" + secrets.token_bytes(32), False
    if isinstance(seed, int):
        return b"int\0" + str(seed).encode("ascii"), True
    if isinstance(seed, str):
        return b"str\0" + seed.encode("utf-8"), True
    if isinstance(seed, (bytes, bytearray, memoryview)):
        return b"bytes\0" + bytes(seed), True
    raise TypeError("seed must be int, str, bytes-like, or None")


def derive_seed_bytes(
    seed_material: bytes,
    algorithm_name: str,
    *,
    length: int = 32,
) -> bytes:
    """Derive algorithm-specific bytes from normalized seed material."""

    algorithm_name = _validate_algorithm_name(algorithm_name)
    if not isinstance(length, int) or isinstance(length, bool) or length <= 0:
        raise ValueError("length must be a positive integer")

    shake = hashlib.shake_256()
    shake.update(_DOMAIN)
    shake.update(len(algorithm_name.encode("utf-8")).to_bytes(4, "big"))
    shake.update(algorithm_name.encode("utf-8"))
    shake.update(len(seed_material).to_bytes(8, "big"))
    shake.update(seed_material)
    return shake.digest(length)


def create_rng(seed: Seed, algorithm_name: str) -> tuple[random.Random, SeedInfo]:
    """Create a deterministic simulation RNG separated by algorithm name.

    When ``seed`` is ``None``, 256 bits of OS entropy are used first. The
    simulation stream itself is produced by ``random.Random`` from a SHAKE-256
    expanded integer seed. The returned RNG is therefore for simulation and
    procedural randomness, not cryptographic use.
    """

    algorithm_name = _validate_algorithm_name(algorithm_name)
    seed_material, deterministic = normalize_seed(seed)
    expanded = derive_seed_bytes(seed_material, algorithm_name, length=32)
    rng_seed = int.from_bytes(expanded, "big")
    fingerprint = hashlib.sha256(seed_material).hexdigest()[:16]
    info = SeedInfo(
        algorithm_name=algorithm_name,
        deterministic=deterministic,
        seed_fingerprint=fingerprint,
    )
    return random.Random(rng_seed), info


__all__ = [
    "Seed",
    "SeedInfo",
    "create_rng",
    "derive_seed_bytes",
    "normalize_seed",
]
