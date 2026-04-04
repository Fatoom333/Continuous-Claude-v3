"""Performance metrics collection for Claude Code runtime.

This module provides metrics collection for monitoring hook performance,
MCP tool calls, and other runtime operations.

Key features:
- Timing decorator for functions
- Hook execution metrics
- Slow operation threshold alerts
- In-memory metrics with optional file persistence
"""

import functools
import logging
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

logger = logging.getLogger("mcp_execution.metrics")

F = TypeVar("F", bound=Callable[..., Any])


# Default threshold for slow operations (in seconds)
DEFAULT_SLOW_THRESHOLD = 5.0


@dataclass
class TimingStats:
    """Statistics for timing measurements."""

    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    times: list[float] = field(default_factory=list)

    @property
    def avg_time(self) -> float:
        """Average execution time."""
        if self.count == 0:
            return 0.0
        return self.total_time / self.count

    @property
    def median_time(self) -> float:
        """Median execution time."""
        if not self.times:
            return 0.0
        return statistics.median(self.times)

    @property
    def p95_time(self) -> float:
        """95th percentile execution time."""
        if len(self.times) < 20:
            return self.max_time
        sorted_times = sorted(self.times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def record(self, duration: float) -> None:
        """Record a timing measurement.

        Args:
            duration: Duration in seconds
        """
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        # Keep last 1000 samples for percentile calculation
        self.times.append(duration)
        if len(self.times) > 1000:
            self.times = self.times[-1000:]


@dataclass
class HookMetrics:
    """Metrics for a single hook."""

    name: str
    timing: TimingStats = field(default_factory=TimingStats)
    errors: int = 0
    slow_count: int = 0
    last_error: str | None = None
    last_slow_duration: float | None = None


@dataclass
class ToolMetrics:
    """Metrics for an MCP tool."""

    server_name: str
    tool_name: str
    timing: TimingStats = field(default_factory=TimingStats)
    errors: int = 0
    circuit_opens: int = 0
    last_error: str | None = None


class MetricsCollector:
    """Central metrics collector for runtime operations.

    Collects timing, error, and performance metrics for:
    - Hook executions
    - MCP tool calls
    - Custom operations

    Usage:
        metrics = MetricsCollector()

        # Time a hook
        with metrics.time_hook("post-tool-use-parallel"):
            # ... hook execution ...

        # Time a tool call
        with metrics.time_tool("github", "search_code"):
            # ... tool call ...

        # Get summary
        summary = metrics.get_summary()
    """

    def __init__(self, slow_threshold: float = DEFAULT_SLOW_THRESHOLD):
        """Initialize metrics collector.

        Args:
            slow_threshold: Threshold in seconds for slow operation warnings
        """
        self.slow_threshold = slow_threshold
        self._hooks: dict[str, HookMetrics] = {}
        self._tools: dict[str, ToolMetrics] = {}
        self._operations: dict[str, TimingStats] = defaultdict(TimingStats)
        self._start_time = time.time()

    def time_hook(self, hook_name: str) -> "TimingContext":
        """Create a timing context for a hook.

        Args:
            hook_name: Name of the hook

        Returns:
            TimingContext for use with 'with' statement
        """
        return TimingContext(self, "hook", hook_name)

    def time_tool(self, server_name: str, tool_name: str) -> "TimingContext":
        """Create a timing context for an MCP tool call.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool

        Returns:
            TimingContext for use with 'with' statement
        """
        return TimingContext(self, "tool", f"{server_name}__{tool_name}")

    def time_operation(self, operation_name: str) -> "TimingContext":
        """Create a timing context for a custom operation.

        Args:
            operation_name: Name of the operation

        Returns:
            TimingContext for use with 'with' statement
        """
        return TimingContext(self, "operation", operation_name)

    def record_hook_timing(
        self, hook_name: str, duration: float, error: Exception | None = None
    ) -> None:
        """Record timing for a hook execution.

        Args:
            hook_name: Name of the hook
            duration: Duration in seconds
            error: Optional exception if hook failed
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = HookMetrics(name=hook_name)

        metrics = self._hooks[hook_name]
        metrics.timing.record(duration)

        if error:
            metrics.errors += 1
            metrics.last_error = str(error)[:200]

        if duration > self.slow_threshold:
            metrics.slow_count += 1
            metrics.last_slow_duration = duration
            logger.warning(
                f"Slow hook '{hook_name}': {duration:.2f}s (threshold: {self.slow_threshold}s)"
            )

    def record_tool_timing(
        self,
        server_name: str,
        tool_name: str,
        duration: float,
        error: Exception | None = None,
        circuit_open: bool = False,
    ) -> None:
        """Record timing for an MCP tool call.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            duration: Duration in seconds
            error: Optional exception if call failed
            circuit_open: Whether circuit breaker was open
        """
        key = f"{server_name}__{tool_name}"

        if key not in self._tools:
            self._tools[key] = ToolMetrics(server_name=server_name, tool_name=tool_name)

        metrics = self._tools[key]
        metrics.timing.record(duration)

        if error:
            metrics.errors += 1
            metrics.last_error = str(error)[:200]

        if circuit_open:
            metrics.circuit_opens += 1

        if duration > self.slow_threshold:
            logger.warning(
                f"Slow tool '{tool_name}' on '{server_name}': {duration:.2f}s "
                f"(threshold: {self.slow_threshold}s)"
            )

    def record_operation_timing(self, operation_name: str, duration: float) -> None:
        """Record timing for a custom operation.

        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
        """
        self._operations[operation_name].record(duration)

        if duration > self.slow_threshold:
            logger.warning(
                f"Slow operation '{operation_name}': {duration:.2f}s "
                f"(threshold: {self.slow_threshold}s)"
            )

    def get_hook_summary(self) -> dict[str, dict[str, Any]]:
        """Get summary of hook metrics.

        Returns:
            Dictionary of hook names to their metrics
        """
        result = {}
        for name, metrics in self._hooks.items():
            result[name] = {
                "count": metrics.timing.count,
                "total_time": metrics.timing.total_time,
                "avg_time": metrics.timing.avg_time,
                "min_time": metrics.timing.min_time if metrics.timing.count > 0 else 0,
                "max_time": metrics.timing.max_time,
                "median_time": metrics.timing.median_time,
                "p95_time": metrics.timing.p95_time,
                "errors": metrics.errors,
                "slow_count": metrics.slow_count,
                "last_error": metrics.last_error,
            }
        return result

    def get_tool_summary(self) -> dict[str, dict[str, Any]]:
        """Get summary of tool metrics.

        Returns:
            Dictionary of tool identifiers to their metrics
        """
        result = {}
        for key, metrics in self._tools.items():
            result[key] = {
                "server": metrics.server_name,
                "tool": metrics.tool_name,
                "count": metrics.timing.count,
                "total_time": metrics.timing.total_time,
                "avg_time": metrics.timing.avg_time,
                "min_time": metrics.timing.min_time if metrics.timing.count > 0 else 0,
                "max_time": metrics.timing.max_time,
                "errors": metrics.errors,
                "circuit_opens": metrics.circuit_opens,
                "last_error": metrics.last_error,
            }
        return result

    def get_summary(self) -> dict[str, Any]:
        """Get full metrics summary.

        Returns:
            Dictionary with all metrics and metadata
        """
        return {
            "uptime_seconds": time.time() - self._start_time,
            "slow_threshold": self.slow_threshold,
            "hooks": self.get_hook_summary(),
            "tools": self.get_tool_summary(),
            "operations": {
                name: {
                    "count": stats.count,
                    "total_time": stats.total_time,
                    "avg_time": stats.avg_time,
                    "min_time": stats.min_time if stats.count > 0 else 0,
                    "max_time": stats.max_time,
                }
                for name, stats in self._operations.items()
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._hooks.clear()
        self._tools.clear()
        self._operations.clear()
        self._start_time = time.time()


class TimingContext:
    """Context manager for timing operations.

    Usage:
        with metrics.time_hook("my-hook"):
            # ... hook code ...
    """

    def __init__(self, collector: MetricsCollector, category: str, name: str):
        """Initialize timing context.

        Args:
            collector: MetricsCollector instance
            category: Category (hook, tool, operation)
            name: Name of the item being timed
        """
        self.collector = collector
        self.category = category
        self.name = name
        self.start_time: float | None = None
        self.error: Exception | None = None

    def __enter__(self) -> "TimingContext":
        """Enter the context, starting the timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context, recording the timing."""
        duration = time.time() - (self.start_time or time.time())

        if exc_val is not None and isinstance(exc_val, Exception):
            self.error = exc_val

        if self.category == "hook":
            self.collector.record_hook_timing(self.name, duration, self.error)
        elif self.category == "tool":
            parts = self.name.split("__", 1)
            if len(parts) == 2:
                self.collector.record_tool_timing(parts[0], parts[1], duration, self.error)
        elif self.category == "operation":
            self.collector.record_operation_timing(self.name, duration)


def timed(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    slow_threshold: float | None = None,
) -> Callable[..., Any]:
    """Decorator to time function execution.

    Can be used with or without arguments:

        @timed
        def my_function():
            ...

        @timed(name="custom_name", slow_threshold=1.0)
        def my_function():
            ...

    Args:
        func: Function to time (if used without parentheses)
        name: Custom name for metrics (default: function name)
        slow_threshold: Threshold for slow warning (default: MetricsCollector default)

    Returns:
        Decorated function
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        operation_name = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = fn(*args, **kwargs)
                return result
            finally:
                global _global_metrics
                duration = time.time() - start_time
                _global_metrics.record_operation_timing(operation_name, duration)

                threshold = slow_threshold or _global_metrics.slow_threshold
                if duration > threshold:
                    logger.warning(
                        f"Slow function '{operation_name}': {duration:.2f}s "
                        f"(threshold: {threshold}s)"
                    )

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


# Global metrics collector instance
_global_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance.

    Returns:
        Global MetricsCollector instance
    """
    return _global_metrics


def reset_metrics() -> None:
    """Reset the global metrics collector."""
    global _global_metrics
    _global_metrics.reset()
