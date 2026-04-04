"""MCP Client Manager with state machine architecture for lazy loading and connection.

This module provides the core runtime client manager that connects to MCP servers
on-demand, caches tools, and manages the lifecycle of server connections using
an explicit state machine pattern for clarity and debugging.

Uses dispatch tables for result unwrapping to reduce cyclomatic complexity.
"""

import asyncio
import json
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import aiofiles
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamablehttp import streamablehttp_client
from mcp.types import Tool

from .config import McpConfig, ServerConfig
from .exceptions import (
    ConfigurationError,
    ServerConnectionError,
    ToolExecutionError,
    ToolNotFoundError,
)

logger = logging.getLogger("mcp_execution.client")


# ===========================================================================
# Retry Configuration - Exponential backoff with jitter
# ===========================================================================


@dataclass
class RetryConfig:
    """Configuration for exponential backoff retry logic.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 0.5)
        max_delay: Maximum delay cap in seconds (default: 30.0)
        backoff_factor: Multiplier for each retry (default: 2.0)
        jitter: Whether to add random jitter (default: True)
    """

    max_retries: int = 3
    initial_delay: float = 0.5
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: bool = True


# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig()

# Error patterns that indicate retryable vs non-retryable errors
RETRYABLE_PATTERNS = [
    "connection reset",
    "connection refused",
    "connection timeout",
    "timed out",
    "timeout",
    "temporary failure",
    "resource temporarily unavailable",
    "rate limit",
    "too many requests",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "internal server error",
    "server error",
]

NON_RETRYABLE_PATTERNS = [
    "not found",
    "invalid parameter",
    "invalid argument",
    "unauthorized",
    "forbidden",
    "access denied",
    "permission denied",
    "authentication failed",
    "invalid api key",
    "tool not found",
    "unsupported operation",
]


def classify_error(error: Exception) -> str:
    """Classify an error as retryable, non-retryable, or unknown.

    Args:
        error: The exception to classify

    Returns:
        "retryable", "non_retryable", or "unknown"
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # Check non-retryable patterns first (more specific)
    for pattern in NON_RETRYABLE_PATTERNS:
        if pattern in error_str or pattern in error_type:
            return "non_retryable"

    # Check retryable patterns
    for pattern in RETRYABLE_PATTERNS:
        if pattern in error_str or pattern in error_type:
            return "retryable"

    # Connection-related exceptions are generally retryable
    if "connection" in error_type or "timeout" in error_type:
        return "retryable"

    # OSError subclasses (network issues) are retryable
    if isinstance(
        error,
        (ConnectionError, ConnectionRefusedError, ConnectionResetError, TimeoutError, OSError),
    ):
        return "retryable"

    return "unknown"


def calculate_backoff_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and optional jitter.

    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    delay = config.initial_delay * (config.backoff_factor**attempt)
    delay = min(delay, config.max_delay)

    if config.jitter:
        # Add up to 25% jitter
        jitter_amount = delay * 0.25
        delay = delay + random.uniform(-jitter_amount, jitter_amount)

    return max(0.1, delay)  # Minimum 100ms


# ===========================================================================
# Project Root Detection - Handles cwd being a subdirectory
# ===========================================================================


def find_project_root(start_dir: Path) -> Path:
    """Find project root by looking for .git directory.

    Walks up from start_dir until finding .git or hitting filesystem root.
    This ensures we find the right directory even if cwd is a subdirectory.

    Args:
        start_dir: Directory to start searching from

    Returns:
        Path to project root (directory containing .git), or start_dir if not found
    """
    current = start_dir.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return start_dir  # Fallback to original if no .git found


# ===========================================================================
# Result Unwrapping Dispatch - Reduces complexity in call_tool
# ===========================================================================


def _unwrap_result(result: Any) -> Any:
    """Unwrap MCP call result using strategy dispatch.

    Tries multiple unwrapping strategies in order:
    1. result.value (most common MCP response format)
    2. result.content (alternative response format)
    3. result itself (raw fallback)

    Args:
        result: Raw MCP tool result

    Returns:
        Unwrapped result value
    """
    # Strategy 1: Try result.value (most common)
    if hasattr(result, "value"):
        return result.value
    # Strategy 2: Try result.content (alternative format)
    if hasattr(result, "content"):
        return result.content
    # Strategy 3: Fall back to result itself
    return result


def _unwrap_text_content(content_list: list[Any]) -> Any:
    """Unwrap text content from MCP response list.

    Handles the common pattern where MCP returns a list with text items.
    Attempts to parse JSON if the text looks like JSON.

    Args:
        content_list: List of content items from MCP response

    Returns:
        Extracted and possibly parsed content
    """
    if not content_list:
        return content_list

    first_item = content_list[0]
    if not hasattr(first_item, "text"):
        return content_list

    text_content = first_item.text

    # Try to parse as JSON if it looks like JSON
    if isinstance(text_content, str) and text_content.strip().startswith(("{", "[")):
        try:
            return json.loads(text_content)
        except json.JSONDecodeError:
            pass

    return text_content


def _unwrap_mcp_response(result: Any) -> Any:
    """Full unwrapping pipeline for MCP responses.

    Combines _unwrap_result and _unwrap_text_content for complete
    response handling.

    Args:
        result: Raw MCP tool result

    Returns:
        Fully unwrapped result value
    """
    unwrapped = _unwrap_result(result)

    # Handle list responses with text content
    if isinstance(unwrapped, list) and len(unwrapped) > 0:
        return _unwrap_text_content(unwrapped)

    return unwrapped


# Dispatch table for result unwrapping strategies
RESULT_UNWRAP_STRATEGIES = [
    ("value", lambda r: r.value),
    ("content", lambda r: r.content),
]


# ===========================================================================
# Config Loading Helpers - Reduces complexity in initialize
# ===========================================================================


async def _load_config_from_path(config_path: str) -> McpConfig:
    """Load MCP config from explicit path.

    Args:
        config_path: Path to config file

    Returns:
        Loaded McpConfig

    Raises:
        ConfigurationError: If load fails
    """
    from pathlib import Path

    path = Path(config_path)
    if not path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")
    try:
        async with aiofiles.open(path) as f:
            content = await f.read()
        return McpConfig.model_validate_json(content)
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in config file {config_path}: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load config from {config_path}: {e}")


def _find_project_config() -> Path | None:
    """Find project config file (.mcp.json or mcp_config.json).

    Returns:
        Path to project config if found, None otherwise
    """
    project_root = find_project_root(Path.cwd())
    mcp_json = project_root / ".mcp.json"
    mcp_config_json = project_root / "mcp_config.json"

    if mcp_json.exists():
        return mcp_json
    elif mcp_config_json.exists():
        return mcp_config_json
    return None


def _merge_configs(global_cfg: McpConfig | None, project_cfg: McpConfig | None) -> McpConfig | None:
    """Merge global and project configs.

    Project config takes precedence for servers with same name.

    Args:
        global_cfg: Global config (may be None)
        project_cfg: Project config (may be None)

    Returns:
        Merged config or None if both are None
    """
    if global_cfg and project_cfg:
        return global_cfg.merge(project_cfg)
    return project_cfg or global_cfg


class ConnectionState(Enum):
    """Explicit states for the MCP Client Manager lifecycle.

    States:
        UNINITIALIZED: Manager created but not initialized
        INITIALIZED: Configuration loaded, no server connections
        CONNECTED: At least one server connection established
    """

    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    CONNECTED = "connected"


class McpClientManager:
    """Lazy-loading MCP client manager with explicit state machine.

    This manager implements a state machine pattern for managing MCP server
    connections with the following characteristics:
    - Lazy initialization: Config loaded on initialize(), servers NOT connected
    - Lazy connection: Servers connect on first call_tool() call
    - Tool caching: Cache tools per server to avoid repeated list_tools calls
    - Defensive unwrapping: Handle response.value and fallback patterns
    - Explicit state tracking: Clear state transitions with validation

    State Transitions:
        UNINITIALIZED -> INITIALIZED (via initialize())
        INITIALIZED -> CONNECTED (via _connect_to_server())
        any state -> UNINITIALIZED (via cleanup())

    Attributes:
        _state: Current connection state
        _clients: Mapping of server names to active client sessions
        _tool_cache: Cached tools per server to avoid repeated queries
        _config: Loaded MCP configuration
        _stdio_contexts: Stdio context managers for proper lifecycle management
        _session_contexts: Session context managers for proper lifecycle management
        _read_streams: Active stdio read streams
        _write_streams: Active stdio write streams
    """

    def __init__(self) -> None:
        """Initialize an uninitialized MCP Client Manager."""
        self._state: ConnectionState = ConnectionState.UNINITIALIZED
        self._clients: dict[str, ClientSession] = {}
        self._tool_cache: dict[str, list[Tool]] = {}
        self._config: McpConfig | None = None
        self._stdio_contexts: dict[str, Any] = {}  # Store stdio context managers
        self._session_contexts: dict[str, Any] = {}  # Store session context managers
        self._read_streams: dict[str, Any] = {}
        self._write_streams: dict[str, Any] = {}

    def _validate_state(self, required_state: ConnectionState, operation: str) -> None:
        """Validate that the manager is in the required state for an operation.

        Args:
            required_state: The state required to perform the operation
            operation: Name of the operation being attempted (for error messages)

        Raises:
            ConfigurationError: If the manager is not in the required state
        """
        if self._state.value != required_state.value:
            raise ConfigurationError(
                f"Cannot {operation}: Manager is in state '{self._state.value}', "
                f"but requires state '{required_state.value}'"
            )

    def _validate_state_at_least(self, minimum_state: ConnectionState, operation: str) -> None:
        """Validate that the manager has at least reached the minimum state.

        Args:
            minimum_state: The minimum state required
            operation: Name of the operation being attempted

        Raises:
            ConfigurationError: If the manager has not reached the minimum state
        """
        state_order = [
            ConnectionState.UNINITIALIZED,
            ConnectionState.INITIALIZED,
            ConnectionState.CONNECTED,
        ]
        current_idx = state_order.index(self._state)
        required_idx = state_order.index(minimum_state)

        if current_idx < required_idx:
            raise ConfigurationError(
                f"Cannot {operation}: Manager is in state '{self._state.value}', "
                f"but requires at least state '{minimum_state.value}'"
            )

    def _mark_initialized(self) -> None:
        """Transition to INITIALIZED state."""
        self._state = ConnectionState.INITIALIZED
        logger.debug("State transition: UNINITIALIZED -> INITIALIZED")

    def _mark_connected(self) -> None:
        """Transition to CONNECTED state."""
        if self._state == ConnectionState.INITIALIZED:
            self._state = ConnectionState.CONNECTED
            logger.debug("State transition: INITIALIZED -> CONNECTED")

    def _mark_uninitialized(self) -> None:
        """Transition back to UNINITIALIZED state."""
        self._state = ConnectionState.UNINITIALIZED
        logger.debug("State transition: -> UNINITIALIZED")

    async def initialize(self, config_path: Path | None = None) -> None:
        """Initialize the manager by loading configuration.

        This method loads the MCP configuration from JSON files but does NOT
        establish any server connections. Connections are established lazily
        on the first tool call.

        Config merging: If both global (~/.claude/mcp_config.json) and project
        configs exist, they are merged with project config taking precedence
        for servers with the same name.

        Args:
            config_path: Optional path to config file. If not provided,
                        merges global config with project config (.mcp.json or mcp_config.json)

        Raises:
            ConfigurationError: If no config file is found or config is invalid
        """
        self._validate_state(ConnectionState.UNINITIALIZED, "initialize")

        # If explicit path provided, use only that
        if config_path:
            if not config_path.exists():
                raise ConfigurationError(f"Config file not found: {config_path}")
            try:
                async with aiofiles.open(config_path) as f:
                    content = await f.read()
                self._config = McpConfig.model_validate_json(content)
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON in config file {config_path}: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to load config from {config_path}: {e}")
        else:
            # Config merging: global + project (project overrides)
            project_root = find_project_root(Path.cwd())
            mcp_json = project_root / ".mcp.json"
            mcp_config_json = project_root / "mcp_config.json"
            global_config = Path.home() / ".claude" / "mcp_config.json"

            global_cfg: McpConfig | None = None
            project_cfg: McpConfig | None = None

            # Load global config if exists
            if global_config.exists():
                try:
                    async with aiofiles.open(global_config) as f:
                        content = await f.read()
                    global_cfg = McpConfig.model_validate_json(content)
                    logger.info(
                        f"Loaded global config: {global_config} ({len(global_cfg.mcpServers)} servers)"
                    )
                except Exception as e:
                    logger.warning(f"Failed to load global config {global_config}: {e}")

            # Load project config if exists (prefer .mcp.json over mcp_config.json)
            project_config_file = None
            if mcp_json.exists():
                project_config_file = mcp_json
            elif mcp_config_json.exists():
                project_config_file = mcp_config_json

            if project_config_file:
                try:
                    async with aiofiles.open(project_config_file) as f:
                        content = await f.read()
                    project_cfg = McpConfig.model_validate_json(content)
                    logger.info(
                        f"Loaded project config: {project_config_file} ({len(project_cfg.mcpServers)} servers)"
                    )
                except json.JSONDecodeError as e:
                    raise ConfigurationError(
                        f"Invalid JSON in config file {project_config_file}: {e}"
                    )
                except Exception as e:
                    raise ConfigurationError(
                        f"Failed to load config from {project_config_file}: {e}"
                    )

            # Merge configs (project overrides global)
            if global_cfg and project_cfg:
                self._config = global_cfg.merge(project_cfg)
                logger.info(f"Merged configs: {len(self._config.mcpServers)} servers total")
            elif project_cfg:
                self._config = project_cfg
            elif global_cfg:
                self._config = global_cfg
            else:
                raise ConfigurationError(
                    f"No config file found. Expected .mcp.json or mcp_config.json in {project_root}, "
                    f"or global config at {global_config}"
                )

        enabled_count = len(self._config.get_enabled_servers())
        logger.info(
            f"Configuration loaded: {len(self._config.mcpServers)} servers total, "
            f"{enabled_count} enabled"
        )
        self._mark_initialized()

    async def _connect_to_server(self, server_name: str, config: ServerConfig) -> None:
        """Establish connection to a single MCP server on-demand.

        This method is called lazily when a tool from the server is first invoked.
        Supports stdio, SSE, and HTTP transports.

        Args:
            server_name: Name of the server to connect to
            config: Server configuration containing connection details

        Raises:
            ServerConnectionError: If connection fails
        """
        if server_name in self._clients:
            logger.debug(f"Server '{server_name}' already connected")
            return

        logger.info(f"Connecting to MCP server: {server_name} (transport: {config.type})")

        try:
            # Create appropriate client based on transport type
            if config.type == "stdio":
                await self._connect_stdio(server_name, config)
            elif config.type == "sse":
                await self._connect_sse(server_name, config)
            elif config.type == "http":
                await self._connect_http(server_name, config)
            else:
                raise ServerConnectionError(f"Unsupported transport type: {config.type}")

            self._mark_connected()
            logger.info(f"Successfully connected to server: {server_name}")

        except Exception as e:
            logger.error(f"Failed to connect to server '{server_name}': {e}")
            # Clean up any partially created contexts
            if server_name in self._stdio_contexts:
                try:
                    await self._stdio_contexts[server_name].__aexit__(None, None, None)
                except Exception:
                    pass
                del self._stdio_contexts[server_name]
            raise ServerConnectionError(f"Could not connect to MCP server '{server_name}': {e}")

    def _substitute_env_vars(self, env: dict[str, str] | None) -> dict[str, str] | None:
        """Substitute ${VAR} placeholders with actual environment variable values."""
        if not env:
            return env
        result = {}
        pattern = re.compile(r"\$\{([^}]+)\}")
        for key, value in env.items():
            # Replace ${VAR} with os.environ.get('VAR', '')
            def replacer(match: re.Match) -> str:
                var_name = match.group(1)
                return os.environ.get(var_name, "")

            result[key] = pattern.sub(replacer, value)
        return result

    async def _connect_stdio(self, server_name: str, config: ServerConfig) -> None:
        """Connect to stdio MCP server."""
        # Substitute environment variable placeholders in config.env
        resolved_env = self._substitute_env_vars(config.env)

        # Merge os.environ with config-specific env vars
        # This ensures API keys loaded from .env are available to subprocess
        # MCP SDK's get_default_environment() only includes basic vars (PATH, HOME, etc.)
        full_env = {**os.environ, **(resolved_env or {})}

        # Create stdio server parameters
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=full_env,
        )

        # Establish stdio connection and store the context manager
        stdio_ctx = stdio_client(server_params)
        streams = await stdio_ctx.__aenter__()
        read_stream, write_stream = streams

        # Store the context manager for cleanup
        self._stdio_contexts[server_name] = stdio_ctx
        self._read_streams[server_name] = read_stream
        self._write_streams[server_name] = write_stream

        # Create and initialize session
        session = ClientSession(read_stream, write_stream)
        client = await session.__aenter__()
        await client.initialize()

        # Store client and session context
        self._clients[server_name] = client
        self._session_contexts[server_name] = session

    async def _connect_sse(self, server_name: str, config: ServerConfig) -> None:
        """Connect to SSE MCP server."""
        # Establish SSE connection
        sse_ctx = sse_client(url=config.url, headers=config.headers or {})
        streams = await sse_ctx.__aenter__()
        read_stream, write_stream = streams

        # Store the context manager for cleanup
        self._stdio_contexts[server_name] = sse_ctx
        self._read_streams[server_name] = read_stream
        self._write_streams[server_name] = write_stream

        # Create and initialize session
        session = ClientSession(read_stream, write_stream)
        client = await session.__aenter__()
        await client.initialize()

        # Store client and session context
        self._clients[server_name] = client
        self._session_contexts[server_name] = session

    async def _connect_http(self, server_name: str, config: ServerConfig) -> None:
        """Connect to Streamable HTTP MCP server."""
        # Establish HTTP connection
        http_ctx = streamablehttp_client(url=config.url, headers=config.headers or {})
        result = await http_ctx.__aenter__()
        # streamablehttp_client returns (read, write, get_session_id)
        read_stream, write_stream, _get_session_id = result

        # Store the context manager for cleanup
        self._stdio_contexts[server_name] = http_ctx
        self._read_streams[server_name] = read_stream
        self._write_streams[server_name] = write_stream

        # Create and initialize session
        session = ClientSession(read_stream, write_stream)
        client = await session.__aenter__()
        await client.initialize()

        # Store client and session context
        self._clients[server_name] = client
        self._session_contexts[server_name] = session

    async def _get_server_tools(self, server_name: str) -> list[Tool]:
        """Get list of tools from a server, using cache if available.

        Args:
            server_name: Name of the server to query

        Returns:
            List of tool objects from the server

        Raises:
            ServerConnectionError: If not connected to the server
        """
        # Check cache first
        if server_name in self._tool_cache:
            logger.debug(f"Using cached tools for server: {server_name}")
            return self._tool_cache[server_name]

        # Ensure we're connected
        if server_name not in self._clients:
            raise ServerConnectionError(f"Not connected to server: {server_name}")

        # Query server for tools
        try:
            client = self._clients[server_name]
            result = await client.list_tools()

            # Defensive unwrapping: handle response.tools
            tools: list[Tool] = result.tools if hasattr(result, "tools") else []

            # Cache the results
            self._tool_cache[server_name] = tools
            logger.debug(f"Cached {len(tools)} tools for server: {server_name}")

            return tools

        except Exception as e:
            logger.error(f"Failed to list tools from server '{server_name}': {e}")
            raise ServerConnectionError(f"Could not list tools from server '{server_name}': {e}")

    async def call_tool(
        self,
        tool_identifier: str,
        params: dict[str, Any],
        max_retries: int | None = None,
        retry_config: RetryConfig | None = None,
    ) -> Any:
        """Call an MCP tool with lazy server connection and exponential backoff retry.

        This is the core method that implements lazy loading. Servers are only
        connected when their tools are first invoked. On failure, automatically
        retries with exponential backoff before raising an error.

        Tool Identifier Format: "serverName__toolName"

        Args:
            tool_identifier: Tool identifier in format "serverName__toolName"
            params: Dictionary of parameters to pass to the tool
            max_retries: (Deprecated) Use retry_config instead. Maximum number of retry attempts.
            retry_config: Optional RetryConfig for custom retry behavior. Uses DEFAULT_RETRY_CONFIG if not provided.

        Returns:
            The tool execution result (unwrapped from response)

        Raises:
            ConfigurationError: If manager not initialized
            ToolNotFoundError: If tool doesn't exist on the specified server
            ToolExecutionError: If tool execution fails after all retries
            ServerConnectionError: If unable to connect to server
        """
        self._validate_state_at_least(ConnectionState.INITIALIZED, "call tool")

        if not self._config:
            raise ConfigurationError("Configuration not loaded")

        # Handle deprecated max_retries parameter
        if max_retries is not None and retry_config is None:
            retry_config = RetryConfig(max_retries=max_retries)
            logger.warning("max_retries is deprecated, use retry_config parameter instead")
        elif retry_config is None:
            retry_config = DEFAULT_RETRY_CONFIG

        # Parse tool identifier
        if "__" not in tool_identifier:
            raise ToolNotFoundError(
                f"Invalid tool identifier '{tool_identifier}'. "
                f"Expected format: 'serverName__toolName'"
            )

        server_name, tool_name = tool_identifier.split("__", 1)

        # Get server configuration
        server_config = self._config.get_server(server_name)
        if not server_config:
            raise ToolNotFoundError(
                f"Server '{server_name}' not found in configuration. "
                f"Available servers: {list(self._config.mcpServers.keys())}"
            )

        if server_config.disabled:
            raise ToolNotFoundError(f"Server '{server_name}' is disabled in configuration")

        # Lazy connection: connect to server if not already connected
        if server_name not in self._clients:
            logger.debug(f"Lazy connecting to server '{server_name}' for tool '{tool_name}'")
            await self._connect_to_server(server_name, server_config)

        # Verify tool exists on server
        tools = await self._get_server_tools(server_name)
        tool_names = [tool.name for tool in tools]

        if tool_name not in tool_names:
            raise ToolNotFoundError(
                f"Tool '{tool_name}' not found on server '{server_name}'. "
                f"Available tools: {tool_names}"
            )

        # Execute the tool with exponential backoff retry logic
        last_error: Exception | None = None

        for attempt in range(retry_config.max_retries + 1):
            try:
                client = self._clients[server_name]
                log_suffix = (
                    f" (attempt {attempt + 1}/{retry_config.max_retries + 1})"
                    if attempt > 0
                    else ""
                )
                logger.info(f"Executing tool: {tool_identifier}{log_suffix}")
                logger.debug(f"Tool parameters: {params}")

                result = await client.call_tool(tool_name, params)

                # Use dispatch-based unwrapping for reduced complexity
                unwrapped = _unwrap_mcp_response(result)

                logger.debug(f"Tool execution result: {unwrapped}")
                return unwrapped

            except Exception as e:
                last_error = e
                error_classification = classify_error(e)

                # Don't retry non-retryable errors
                if error_classification == "non_retryable":
                    logger.error(f"Non-retryable error for '{tool_identifier}': {e}")
                    raise ToolExecutionError(
                        f"Tool execution failed for '{tool_identifier}' (non-retryable): {e}"
                    ) from e

                if attempt < retry_config.max_retries:
                    delay = calculate_backoff_delay(attempt, retry_config)
                    error_type = type(e).__name__

                    print(
                        f"⚠️  MCP call failed (attempt {attempt + 1}/{retry_config.max_retries + 1}), "
                        f"retrying in {delay:.2f}s... [{error_type}: {e}]",
                        file=sys.stderr,
                    )
                    logger.warning(
                        f"Tool execution attempt {attempt + 1} failed for '{tool_identifier}' "
                        f"(classified as {error_classification}): {e}. Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Tool execution failed after {retry_config.max_retries + 1} attempts "
                        f"for '{tool_identifier}': {e}"
                    )

        # All retries exhausted
        print(
            f"❌ MCP call failed after {retry_config.max_retries + 1} attempts: {last_error}",
            file=sys.stderr,
        )
        raise ToolExecutionError(
            f"Failed to execute tool '{tool_identifier}' after {retry_config.max_retries + 1} attempts: {last_error}"
        )

    async def list_all_tools(self) -> list[Tool]:
        """List all available tools from all enabled servers.

        This method connects to all enabled servers to retrieve their tool lists.
        Results are cached per server to avoid repeated queries.

        Returns:
            List of all available tools across all enabled servers

        Raises:
            ConfigurationError: If manager not initialized
            ServerConnectionError: If unable to connect to any server
        """
        self._validate_state_at_least(ConnectionState.INITIALIZED, "list all tools")

        if not self._config:
            raise ConfigurationError("Configuration not loaded")

        all_tools: list[Tool] = []
        enabled_servers = self._config.get_enabled_servers()

        if not enabled_servers:
            logger.warning("No enabled servers configured")
            return all_tools

        logger.info(f"Listing tools from {len(enabled_servers)} enabled servers")

        for server_name, server_config in enabled_servers.items():
            try:
                # Connect to server if not already connected
                if server_name not in self._clients:
                    await self._connect_to_server(server_name, server_config)

                # Get tools from server (uses cache if available)
                tools = await self._get_server_tools(server_name)
                all_tools.extend(tools)
                logger.debug(f"Server '{server_name}': {len(tools)} tools")

            except Exception as e:
                logger.error(f"Failed to list tools from server '{server_name}': {e}")
                # Continue with other servers rather than failing completely

        logger.info(f"Total tools available: {len(all_tools)}")
        return all_tools

    async def cleanup(self) -> None:
        """Close all connections and reset manager to uninitialized state.

        This method gracefully closes all active server connections and clears
        all cached data, returning the manager to UNINITIALIZED state.
        """
        logger.info("Cleaning up MCP Client Manager")

        # Properly exit all session contexts
        for server_name in list(self._session_contexts.keys()):
            try:
                session_ctx = self._session_contexts[server_name]
                await session_ctx.__aexit__(None, None, None)
                logger.debug(f"Closed session context for server: {server_name}")
            except (RuntimeError, asyncio.CancelledError) as e:
                # Ignore cancel scope errors that can occur when contexts are entered
                # and exited in different event loop tasks (e.g., when scripts call asyncio.run())
                if "cancel scope" in str(e).lower() or isinstance(e, asyncio.CancelledError):
                    logger.debug(
                        f"Ignoring cancel scope error during cleanup for '{server_name}': {e}"
                    )
                else:
                    logger.error(f"Error closing session context for '{server_name}': {e}")
            except Exception as e:
                logger.error(f"Error closing session context for '{server_name}': {e}")

        # Properly exit all stdio contexts
        for server_name in list(self._stdio_contexts.keys()):
            try:
                stdio_ctx = self._stdio_contexts[server_name]
                await stdio_ctx.__aexit__(None, None, None)
                logger.debug(f"Closed stdio context for server: {server_name}")
            except (RuntimeError, asyncio.CancelledError) as e:
                # Ignore cancel scope errors that can occur when contexts are entered
                # and exited in different event loop tasks (e.g., when scripts call asyncio.run())
                if "cancel scope" in str(e).lower() or isinstance(e, asyncio.CancelledError):
                    logger.debug(
                        f"Ignoring cancel scope error during cleanup for '{server_name}': {e}"
                    )
                else:
                    logger.error(f"Error closing stdio context for '{server_name}': {e}")
            except Exception as e:
                logger.error(f"Error closing stdio context for '{server_name}': {e}")

        # Clear all state
        self._clients.clear()
        self._session_contexts.clear()
        self._stdio_contexts.clear()
        self._tool_cache.clear()
        self._read_streams.clear()
        self._write_streams.clear()
        self._config = None
        self._mark_uninitialized()

        logger.info("Cleanup complete")


# Singleton pattern using lru_cache (thread-safe)
@lru_cache(maxsize=1)
def get_mcp_client_manager() -> McpClientManager:
    """Get or create the singleton MCP Client Manager instance.

    This function uses functools.lru_cache to ensure only one instance
    of the manager exists, providing thread-safe singleton behavior.

    Returns:
        The singleton McpClientManager instance
    """
    logger.debug("Getting MCP Client Manager singleton")
    return McpClientManager()


async def call_mcp_tool(
    tool_identifier: str,
    params: dict[str, Any],
    max_retries: int | None = None,
    retry_config: RetryConfig | None = None,
) -> Any:
    """Convenience function for calling MCP tools using the singleton manager.

    This is a high-level API that automatically uses the singleton manager instance.
    On failure, automatically retries with exponential backoff before raising an error.

    Args:
        tool_identifier: Tool identifier in format "serverName__toolName"
        params: Dictionary of parameters to pass to the tool
        max_retries: (Deprecated) Use retry_config instead. Maximum number of retry attempts.
        retry_config: Optional RetryConfig for custom retry behavior. Uses DEFAULT_RETRY_CONFIG if not provided.

    Returns:
        The tool execution result

    Raises:
        ConfigurationError: If manager not initialized
        ToolNotFoundError: If tool doesn't exist
        ToolExecutionError: If tool execution fails after all retries
        ServerConnectionError: If unable to connect to server
    """
    manager = get_mcp_client_manager()
    return await manager.call_tool(
        tool_identifier, params, max_retries=max_retries, retry_config=retry_config
    )
