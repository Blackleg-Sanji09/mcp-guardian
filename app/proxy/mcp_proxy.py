import asyncio
import sys
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent

from app.approval.manager import ApprovalManager
from app.approval.models import ApprovalStatus
from app.ui.popup_manager import PopupManager


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
        approval_manager = ApprovalManager()
        loop = asyncio.get_running_loop()
        popup_manager = PopupManager(loop)

        # Forward tool discovery requests to the original server.
        async def handle_list_tools(context, params):
            print("Received tool discovery request.", file=sys.stderr)

            return await upstream_session.list_tools(params=params)

        # Handle tool invocation requests.
        async def handle_call_tool(context, params):
            # Create an approval request.
            request = approval_manager.create_request(
                tool_name=params.name,
                arguments=params.arguments or {},
            )

            print(
                f"\nApproval required for: {request.tool_name}",
                file=sys.stderr,
            )

            print(
                f"Request ID: {request.request_id}",
                file=sys.stderr,
            )

            print(
                f"Arguments: {request.arguments}",
                file=sys.stderr,
            )

            # Display the approval popup.
            popup_manager.show_popup(
                request_id=request.request_id,
                tool_name=request.tool_name,
                arguments=request.arguments,
                approval_manager=approval_manager,
            )

            # Wait until the request receives a decision.
            await approval_manager.wait_for_decision(request.request_id)

            # Forward only approved requests.
            if request.status == ApprovalStatus.APPROVED:
                print(
                    "Request approved. Forwarding to upstream server.",
                    file=sys.stderr,
                )

                return await upstream_session.call_tool(
                    name=params.name,
                    arguments=params.arguments,
                )

            # Blocked requests never reach the upstream server.
            print("Request blocked.", file=sys.stderr)

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Tool execution blocked by MCP Guardian.",
                    )
                ],
                isError=True,
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