"""
Script execution harness for MCP-enabled Python scripts.

This harness:
1. Initializes MCP client manager
2. Executes user script with MCP tools available
3. Handles signals gracefully (SIGINT/SIGTERM)
4. Cleans up all connections on exit
"""

import asyncio
import logging
import runpy
import signal
import sys
from pathlib import Path
from typing import Any, NoReturn

from .env_utils import load_project_env
from .exceptions import McpExecutionError
from .mcp_client import get_mcp_client_manager

# Configure logging to stderr
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stderr)

logger = logging.getLogger("mcp_execution.harness")


# ===========================================================================
# Error Pattern Classification
# ===========================================================================

# Known harmless error patterns from MCP SDK asyncgen cleanup
HARMLESS_ASYNCGEN_PATTERNS = [
    "asynchronous generator",
    "asyncgen",
    "cancel scope",
    "attempted to cancel",
    "cancel scope stack",
    "cancel scope mismatch",
]

# Patterns that indicate real problems that should NOT be suppressed
REAL_ERROR_PATTERNS = [
    "traceback",
    "error in",
    "exception in",
    "failed to",
    "connection refused",
    "connection reset",
    "permission denied",
    "file not found",
    "module not found",
    "import error",
]


def is_harmless_asyncgen_error(message: str, exception: Exception | None) -> bool:
    """Check if an error is a harmless asyncgen/cancel scope cleanup artifact.

    These errors occur when MCP SDK's async generators are cleaned up in
    different task contexts. They are harmless and should be suppressed.

    Args:
        message: Log message or error string
        exception: Optional exception object for additional context

    Returns:
        True if the error is harmless and should be suppressed
    """
    msg_lower = message.lower()

    # Check if any harmless pattern matches
    for pattern in HARMLESS_ASYNCGEN_PATTERNS:
        if pattern in msg_lower:
            # Verify it's not masking a real error
            for real_pattern in REAL_ERROR_PATTERNS:
                if real_pattern in msg_lower:
                    return False
            return True

    # Check exception type
    if exception:
        exc_type = type(exception).__name__.lower()
        if "cancel" in exc_type:
            return True

    return False


class SelectiveAsyncgenFilter(logging.Filter):
    """Filter that selectively suppresses harmless asyncgen cleanup errors.

    Unlike blanket suppression, this filter checks each log record to ensure
    we only suppress known harmless patterns, not real errors.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()

        # Get exception if present
        exception = getattr(record, "exc_info", None)
        exc_obj = exception[1] if exception else None

        # Suppress only if it's a harmless asyncgen error
        if is_harmless_asyncgen_error(message, exc_obj):
            logger.debug(f"Suppressed harmless asyncgen error: {message[:100]}")
            return False

        return True


def _parse_arguments() -> Path:
    """
    Parse command-line arguments.

    Returns:
        Path to script
    """
    if len(sys.argv) < 2:
        logger.error("Usage: python -m runtime.harness <script_path>")
        sys.exit(1)

    return Path(sys.argv[1]).resolve()


# Handler for selective asyncgen error suppression (set by _suppress_asyncgen_errors)
_asyncgen_handler = None


def _suppress_asyncgen_errors():
    """
    Install selective asyncgen cleanup error handling.

    Unlike blanket suppression, this uses pattern matching to only suppress
    known harmless errors while preserving real error visibility.

    This function:
    1. Adds SelectiveAsyncgenFilter to asyncio logger
    2. Creates a handler that only suppresses harmless patterns
    3. Stores handler for use in event loops
    """
    global _asyncgen_handler

    # Add selective filter to asyncio logger
    asyncio_logger = logging.getLogger("asyncio")
    asyncio_logger.addFilter(SelectiveAsyncgenFilter())

    # Define selective exception handler
    def selective_exception_handler(loop, context):
        """Handle exceptions selectively - suppress only harmless asyncgen errors."""
        exception = context.get("exception")
        message = context.get("message", "")

        # Check if this is a harmless asyncgen error
        if is_harmless_asyncgen_error(message, exception):
            logger.debug(f"Suppressed asyncgen error in loop handler: {message[:100]}")
            return

        # For all other exceptions, use default handler
        loop.default_exception_handler(context)

    # Store handler globally for use in _execute_direct
    _asyncgen_handler = selective_exception_handler


def _execute_direct(script_path: Path) -> int:
    """
    Execute script in direct mode (current process, no sandbox).

    Args:
        script_path: Path to Python script

    Returns:
        Exit code
    """
    logger.info("=== Direct Mode ===")

    # Add project root and src/ to Python path for imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        logger.debug(f"Added to sys.path: {src_path}")

    project_root = src_path.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.debug(f"Added to sys.path: {project_root}")

    # Suppress asyncgen cleanup errors from MCP SDK
    # This must be done BEFORE any event loop is created
    _suppress_asyncgen_errors()

    # Create persistent event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Set exception handler to suppress asyncgen errors
    if _asyncgen_handler is not None:
        loop.set_exception_handler(_asyncgen_handler)

    # Initialize MCP client manager
    manager = get_mcp_client_manager()
    try:
        loop.run_until_complete(manager.initialize())
        logger.info("MCP client manager initialized")
    except McpExecutionError as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        return 1

    # Set up signal handling
    def signal_handler(signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down...")
        sys.exit(130)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Execute script
    exit_code = 0
    try:
        logger.info(f"Executing script: {script_path}")
        runpy.run_path(str(script_path), run_name="__main__")
        logger.info("Script execution completed")

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        exit_code = 130

    except Exception as e:
        logger.error(f"Script execution failed: {e}", exc_info=True)
        exit_code = 1

    finally:
        # Cleanup
        logger.debug("Cleaning up MCP connections...")
        try:
            loop.run_until_complete(manager.cleanup())
            logger.info("Cleanup complete")
        except BaseException as e:
            # Suppress BaseExceptionGroup from async generators
            if type(e).__name__ == "BaseExceptionGroup":
                logger.debug("Suppressed BaseExceptionGroup during cleanup")
            else:
                logger.error(f"Cleanup failed: {e}", exc_info=True)
                if exit_code == 0:
                    exit_code = 1
        finally:
            # Reset asyncgen hooks before closing loop
            sys.set_asyncgen_hooks(firstiter=None, finalizer=None)
            loop.close()

    return exit_code


def main() -> NoReturn:
    """Entry point for the harness."""
    # 0. Load .env file (if present) for API keys
    if load_project_env():
        logger.info("Loaded .env file")

    # 1. Parse CLI arguments
    script_path = _parse_arguments()

    # 2. Validate script exists
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        sys.exit(1)

    if not script_path.is_file():
        logger.error(f"Not a file: {script_path}")
        sys.exit(1)

    logger.info(f"Script: {script_path}")

    # 3. Execute script
    exit_code = _execute_direct(script_path)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
