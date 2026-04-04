"""Circuit Breaker pattern implementation for resilient MCP server connections.

The Circuit Breaker prevents cascading failures by temporarily blocking requests
to a failing service, allowing it time to recover.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failing, requests are blocked, timer waits for recovery
- HALF_OPEN: Testing recovery, limited requests allowed

Configuration:
- failure_threshold: Number of failures before opening (default: 5)
- recovery_timeout: Seconds to wait before attempting recovery (default: 30)
- half_open_max_calls: Max test calls in HALF_OPEN state (default: 3)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Callable

logger = logging.getLogger("mcp_execution.circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitStats:
    """Statistics for circuit breaker monitoring."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: float | None = None
    last_failure_message: str | None = None
    state_transitions: list[tuple[float, CircuitState, CircuitState]] = field(default_factory=list)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior.

    Attributes:
        failure_threshold: Number of consecutive failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        half_open_max_calls: Max calls allowed in HALF_OPEN state
        success_threshold: Consecutive successes needed to close from HALF_OPEN
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2


class CircuitBreaker:
    """Thread-safe circuit breaker implementation.

    The circuit breaker protects against cascading failures by:
    1. Tracking consecutive failures
    2. Opening when threshold is exceeded
    3. Allowing recovery after timeout
    4. Testing recovery with limited requests

    Example:
        breaker = CircuitBreaker("github-server")

        async def call_with_protection():
            if breaker.should_allow():
                try:
                    result = await call_server()
                    breaker.record_success()
                    return result
                except Exception as e:
                    breaker.record_failure(e)
                    raise
            else:
                raise CircuitOpenError(breaker.name, breaker.stats)
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        """Initialize circuit breaker.

        Args:
            name: Identifier for this circuit (e.g., server name)
            config: Configuration options, uses defaults if not provided
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = Lock()
        self._stats = CircuitStats()
        self._opened_at: float | None = None

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def stats(self) -> CircuitStats:
        """Circuit breaker statistics."""
        return self._stats

    def should_allow(self) -> bool:
        """Check if a request should be allowed through.

        Returns:
            True if request should proceed, False if circuit is open

        Raises:
            Never raises - returns False instead of raising to allow
            caller to handle gracefully
        """
        with self._lock:
            self._stats.total_calls += 1

            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if self._opened_at is None:
                    self._opened_at = time.time()

                elapsed = time.time() - self._opened_at
                if elapsed >= self.config.recovery_timeout:
                    # Transition to HALF_OPEN
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_calls = 0
                    return True

                # Still in cooldown
                self._stats.rejected_calls += 1
                logger.debug(
                    f"Circuit '{self.name}' OPEN, rejecting request "
                    f"(recovery in {self.config.recovery_timeout - elapsed:.1f}s)"
                )
                return False

            if self._state == CircuitState.HALF_OPEN:
                # Allow limited requests in HALF_OPEN
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                else:
                    self._stats.rejected_calls += 1
                    logger.debug(
                        f"Circuit '{self.name}' HALF_OPEN, max calls ({self.config.half_open_max_calls}) reached"
                    )
                    return False

        return True  # Should never reach here

    def record_success(self) -> None:
        """Record a successful operation."""
        with self._lock:
            self._stats.successful_calls += 1

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    # Enough successes, close the circuit
                    self._transition_to(CircuitState.CLOSED)
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(
                        f"Circuit '{self.name}' CLOSED after {self._success_count} successful calls"
                    )

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def record_failure(self, error: Exception) -> None:
        """Record a failed operation.

        Args:
            error: The exception that occurred
        """
        with self._lock:
            self._stats.failed_calls += 1
            self._stats.last_failure_time = time.time()
            self._stats.last_failure_message = str(error)
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failure in HALF_OPEN, reopen immediately
                self._transition_to(CircuitState.OPEN)
                self._success_count = 0
                logger.warning(
                    f"Circuit '{self.name}' reopened after failure in HALF_OPEN: {error}"
                )

            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.warning(
                        f"Circuit '{self.name}' OPENED after {self._failure_count} consecutive failures"
                    )

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state and log the transition."""
        old_state = self._state
        self._state = new_state

        if new_state == CircuitState.OPEN:
            self._opened_at = time.time()
        elif new_state == CircuitState.CLOSED:
            self._opened_at = None

        # Record transition for monitoring
        self._stats.state_transitions.append((time.time(), old_state, new_state))

        logger.info(f"Circuit '{self.name}' transitioned: {old_state.value} -> {new_state.value}")

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._opened_at = None
            self._stats = CircuitStats()
            logger.info(f"Circuit '{self.name}' reset to CLOSED")

    def is_open(self) -> bool:
        """Check if circuit is currently open (blocking requests)."""
        return self._state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        """Check if circuit is in half-open state (testing recovery)."""
        return self._state == CircuitState.HALF_OPEN

    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED


class CircuitBreakerManager:
    """Manages circuit breakers for multiple MCP servers.

    Provides a registry of circuit breakers keyed by server name,
    ensuring consistent circuit breaker instances across calls.

    Example:
        manager = CircuitBreakerManager()

        # Get or create circuit breaker for a server
        breaker = manager.get_breaker("github")

        # Check circuit state before calling
        if breaker.should_allow():
            try:
                result = await call_server()
                breaker.record_success()
            except Exception as e:
                breaker.record_failure(e)
                raise
        else:
            raise CircuitOpenError("github", breaker.stats)
    """

    def __init__(self, default_config: CircuitBreakerConfig | None = None):
        """Initialize circuit breaker manager.

        Args:
            default_config: Default configuration for new circuit breakers
        """
        self._breakers: dict[str, CircuitBreaker] = {}
        self._default_config = default_config or CircuitBreakerConfig()
        self._lock = Lock()

    def get_breaker(self, name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
        """Get or create a circuit breaker for a server.

        Args:
            name: Server name
            config: Optional custom config, uses default if not provided

        Returns:
            CircuitBreaker instance for the server
        """
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    config=config or self._default_config,
                )
            return self._breakers[name]

    def get_all_stats(self) -> dict[str, CircuitStats]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {name: breaker.stats for name, breaker in self._breakers.items()}

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()

    def remove_breaker(self, name: str) -> bool:
        """Remove a circuit breaker from the registry.

        Args:
            name: Server name

        Returns:
            True if breaker was removed, False if not found
        """
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                return True
            return False


# Singleton instance for use across the application
_circuit_breaker_manager: CircuitBreakerManager | None = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get the singleton circuit breaker manager instance."""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager()
    return _circuit_breaker_manager
