import asyncio
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Original MCP server (temporary test server)
UPSTREAM_SERVER = PROJECT_ROOT / "tests" / "fixtures" / "test_mcp_server.py"


@asynccontextmanager
async def connect_to_upstream() -> AsyncIterator[ClientSession]:
    """Connect to the original MCP server and maintain the connection."""

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(UPSTREAM_SERVER)],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            print("Connected to upstream MCP server!", file=sys.stderr)

            yield session


async def main():
    """Run MCP Guardian as a proxy server."""

    async with connect_to_upstream() as upstream_session:

        # Forward tool discovery requests to the original server.
        async def handle_list_tools(context, params):
            print("Received tool discovery request.", file=sys.stderr)

            return await upstream_session.list_tools(params=params)

        # Forward tool invocation requests to the original server.
        async def handle_call_tool(context, params):
            print(
                f"Forwarding tool call: {params.name}",
                file=sys.stderr,
            )

            print(
                f"Arguments: {params.arguments}",
                file=sys.stderr,
            )

            return await upstream_session.call_tool(
                name=params.name,
                arguments=params.arguments,
            )

        # Create Guardian's downstream MCP server.
        guardian = Server(
            "MCP Guardian",
            version="0.1.0",
            on_list_tools=handle_list_tools,
            on_call_tool=handle_call_tool,
        )

        # Accept MCP communication from Claude Desktop.
        async with stdio_server() as (read_stream, write_stream):
            print("MCP Guardian is running.", file=sys.stderr)

            await guardian.run(
                read_stream,
                write_stream,
                guardian.create_initialization_options(),
            )


if __name__ == "__main__":
    asyncio.run(main())