"""Custom exception classes for MCP Code Execution runtime.

This module defines the exception hierarchy for handling various error
conditions in the MCP execution environment.
"""


class McpExecutionError(Exception):
    """Base exception for all MCP execution errors."""

    pass


class ServerConnectionError(McpExecutionError):
    """Raised when unable to connect to an MCP server.

    This typically indicates issues with server availability, configuration,
    or network connectivity.
    """

    pass


class ToolNotFoundError(McpExecutionError):
    """Raised when a requested tool does not exist on any configured server.

    This can occur if:
    - The tool name is misspelled
    - The server providing the tool is not configured
    - The tool has been removed from the server
    """

    pass


class ToolExecutionError(McpExecutionError):
    """Raised when tool execution fails.

    This wraps errors that occur during the actual execution of a tool,
    such as invalid parameters, permission issues, or internal tool errors.
    """

    pass


class ConfigurationError(McpExecutionError):
    """Raised when there are issues with configuration files or settings.

    This includes:
    - Invalid JSON in mcp_config.json
    - Missing required configuration fields
    - Invalid configuration values
    """

    pass


class SchemaValidationError(McpExecutionError):
    """Raised when schema validation fails.

    This occurs when:
    - Response data doesn't match expected schema
    - Input parameters fail validation
    - JSON Schema to Pydantic conversion fails
    """

    pass


class CircuitOpenError(McpExecutionError):
    """Raised when a circuit breaker is open and blocking requests.

    This indicates that a server has been failing repeatedly and the
    circuit breaker has opened to prevent cascading failures.

    Attributes:
        server_name: Name of the server with open circuit
        stats: Circuit breaker statistics at time of rejection
    """

    def __init__(self, server_name: str, stats: "CircuitStats"):
        self.server_name = server_name
        self.stats = stats
        super().__init__(
            f"Circuit breaker OPEN for server '{server_name}': "
            f"{stats.failed_calls} failures, last error: {stats.last_failure_message}"
        )
