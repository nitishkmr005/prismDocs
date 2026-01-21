"""Thread-safe singleton metaclass.

This module provides a metaclass for implementing the singleton pattern,
replacing the scattered singleton boilerplate in service files.
"""

from threading import Lock
from typing import Any, TypeVar

T = TypeVar("T")


class SingletonMeta(type):
    """Thread-safe singleton metaclass.

    Use this metaclass to ensure only one instance of a class exists.
    Thread-safe for concurrent access.

    Example:
        >>> class MyService(metaclass=SingletonMeta):
        ...     def __init__(self, config: str):
        ...         self.config = config
        ...
        >>> # First call creates instance
        >>> service1 = MyService("config_a")
        >>> # Second call returns same instance
        >>> service2 = MyService("config_b")
        >>> assert service1 is service2
        >>> assert service1.config == "config_a"
    """

    _instances: dict[type, Any] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Get or create the singleton instance.

        Thread-safe implementation using double-checked locking.

        Args:
            *args: Arguments passed to __init__ (only used on first call)
            **kwargs: Keyword arguments passed to __init__ (only used on first call)

        Returns:
            The singleton instance
        """
        # Fast path: instance already exists
        if cls in cls._instances:
            return cls._instances[cls]

        # Slow path: acquire lock and create instance
        with cls._lock:
            # Double-check after acquiring lock
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

    @classmethod
    def reset(cls, target_class: type) -> None:
        """Reset a singleton instance (useful for testing).

        Args:
            target_class: The class whose singleton to reset
        """
        with cls._lock:
            cls._instances.pop(target_class, None)

    @classmethod
    def reset_all(cls) -> None:
        """Reset all singleton instances (useful for testing)."""
        with cls._lock:
            cls._instances.clear()


def get_or_create_singleton(
    singleton_instance: T | None,
    factory: type[T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Utility function for simple singleton pattern.

    Alternative to SingletonMeta for cases where metaclass isn't suitable.

    Args:
        singleton_instance: Current singleton instance (may be None)
        factory: Class to instantiate if singleton doesn't exist
        *args: Arguments for factory
        **kwargs: Keyword arguments for factory

    Returns:
        The singleton instance

    Example:
        >>> _instance: MyService | None = None
        >>> def get_service() -> MyService:
        ...     global _instance
        ...     _instance = get_or_create_singleton(_instance, MyService)
        ...     return _instance
    """
    if singleton_instance is None:
        return factory(*args, **kwargs)
    return singleton_instance
