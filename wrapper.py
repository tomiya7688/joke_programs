"""Registry and invocation wrapper for the exotic random generators."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


Factory = Callable[..., Any]


class ExoticRandomWrapper:
    """Create and call named generator instances through one small API.

    A factory is registered once, then its instance can be created and called
    by name. The wrapper does not assume that every algorithm has the same
    constructor or output method.
    """

    def __init__(self, factories: Mapping[str, Factory] | None = None) -> None:
        self._factories: dict[str, Factory] = {}
        self._instances: dict[str, Any] = {}
        if factories is not None:
            for name, factory in factories.items():
                self.register(name, factory)

    def register(self, name: str, factory: Factory, *, replace: bool = False) -> None:
        """Register a named factory."""

        self._validate_name(name)
        if not callable(factory):
            raise TypeError("factory must be callable")
        if name in self._factories and not replace:
            raise ValueError(f"generator is already registered: {name}")
        self._factories[name] = factory
        self._instances.pop(name, None)

    def available(self) -> tuple[str, ...]:
        """Return registered generator names in stable order."""

        return tuple(sorted(self._factories))

    def create(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Create and remember an instance for a registered generator."""

        factory = self._factories.get(name)
        if factory is None:
            raise KeyError(f"unknown generator: {name}")
        instance = factory(*args, **kwargs)
        self._instances[name] = instance
        return instance

    def get(self, name: str) -> Any:
        """Return a previously created instance."""

        if name not in self._instances:
            raise RuntimeError(f"generator has not been created: {name}")
        return self._instances[name]

    def invoke(
        self,
        name: str,
        *args: Any,
        method: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke one named instance.

        If method is omitted, next(), random(), or generate() is selected in
        that order. A callable instance is used as a final fallback.
        """

        instance = self.get(name)
        if method is not None:
            return self._invoke_member(instance, method, args, kwargs)

        for candidate in ("next", "random", "generate"):
            member = getattr(instance, candidate, None)
            if callable(member):
                return member(*args, **kwargs)
        if callable(instance):
            return instance(*args, **kwargs)
        raise TypeError(
            f"{name} has no callable next(), random(), generate(), or __call__()"
        )

    def invoke_all(self, methods: Mapping[str, str] | None = None) -> dict[str, Any]:
        """Invoke every created instance and return results keyed by name."""

        methods = {} if methods is None else methods
        return {
            name: self.invoke(name, method=methods.get(name))
            for name in sorted(self._instances)
        }

    def clear(self) -> None:
        """Forget created instances while keeping factory registrations."""

        self._instances.clear()

    @staticmethod
    def _invoke_member(
        instance: Any,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        member = getattr(instance, method)
        if callable(member):
            return member(*args, **kwargs)
        if args or kwargs:
            raise TypeError(f"{method} is not callable")
        return member

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("generator name must be a non-empty string")


def create_default_wrapper() -> ExoticRandomWrapper:
    """Return a wrapper with the currently available Frog type registered."""

    from frog import Frog

    return ExoticRandomWrapper({"frog": Frog})


__all__ = ["ExoticRandomWrapper", "create_default_wrapper"]
