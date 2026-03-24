"""
Tool protocol.

Defines the contract for tools that agents can use to accomplish tasks.
Tools are the building blocks of agent capabilities - they represent
discrete actions an agent can take.

Example:
    from dynabots_core import Tool

    class DatabaseSearchTool:
        @property
        def name(self) -> str:
            return "search_database"

        @property
        def description(self) -> str:
            return "Search the database for records matching the query"

        @property
        def parameters_schema(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "table": {
                        "type": "string",
                        "enum": ["users", "orders", "products"]
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "maximum": 100
                    }
                },
                "required": ["query", "table"]
            }

        async def execute(self, query: str, table: str, limit: int = 10) -> list:
            return await self.db.search(table, query, limit)
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    """
    Protocol for tools that agents can execute.

    Tools represent discrete capabilities that agents can invoke.
    They have a name, description, parameter schema, and execute method.

    The parameter schema follows JSON Schema format, enabling:
    - Validation of inputs
    - Auto-generation of documentation
    - LLM function calling integration

    Required properties:
    - name: Unique tool identifier
    - description: What the tool does (for LLM understanding)
    - parameters_schema: JSON Schema for parameters

    Required methods:
    - execute: Run the tool with given parameters

    Example implementation:
        class SendEmailTool:
            @property
            def name(self) -> str:
                return "send_email"

            @property
            def description(self) -> str:
                return "Send an email to the specified recipient"

            @property
            def parameters_schema(self) -> dict:
                return {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "format": "email"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to", "subject", "body"]
                }

            async def execute(self, to: str, subject: str, body: str) -> dict:
                await self.email_client.send(to=to, subject=subject, body=body)
                return {"status": "sent", "to": to}
    """

    @property
    def name(self) -> str:
        """Unique tool identifier."""
        ...

    @property
    def description(self) -> str:
        """
        Human-readable description of what this tool does.

        This is shown to LLMs to help them understand when to use the tool.
        Be specific and include examples of when to use/not use it.
        """
        ...

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """
        JSON Schema for the tool's parameters.

        Returns:
            Dictionary following JSON Schema specification.

        Example:
            {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        """
        ...

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the given parameters.

        Args:
            **kwargs: Parameters matching the parameters_schema.

        Returns:
            Tool execution result (type depends on the specific tool).

        Raises:
            ValueError: If parameters are invalid.
            Exception: Tool-specific errors.
        """
        ...


def tool_to_openai_format(tool: Tool) -> Dict[str, Any]:
    """
    Convert a Tool to OpenAI function calling format.

    Args:
        tool: Tool instance to convert.

    Returns:
        Dictionary in OpenAI's function format.

    Example:
        openai_tool = tool_to_openai_format(my_tool)
        # Returns:
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "my_tool",
        #         "description": "...",
        #         "parameters": {...}
        #     }
        # }
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters_schema,
        },
    }


def tool_to_anthropic_format(tool: Tool) -> Dict[str, Any]:
    """
    Convert a Tool to Anthropic tool format.

    Args:
        tool: Tool instance to convert.

    Returns:
        Dictionary in Anthropic's tool format.
    """
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.parameters_schema,
    }
