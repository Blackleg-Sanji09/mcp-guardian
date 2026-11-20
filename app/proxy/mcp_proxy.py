import asyncio
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent

from app.approval.manager import ApprovalManager
from app.approval.models import ApprovalStatus
from app.ui.popup_manager import PopupManager


PROJECT_ROOT = Path(__file__).resolve().parents[2]

UPSTREAM_SERVER = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "test_mcp_server.py"
)

APPROVAL_TIMEOUT = 120


@asynccontextmanager
async def connect_to_upstream() -> AsyncIterator[ClientSession]:
    """Connect to the original MCP server."""

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(UPSTREAM_SERVER)],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_params) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
            await session.initialize()

            print(
                "Connected to upstream MCP server!",
                file=sys.stderr,
            )

            yield session


def create_error_result(message: str) -> CallToolResult:
    """Create an MCP tool error response."""

    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=message,
            )
        ],
        isError=True,
    )


async def main() -> None:
    """Run MCP Guardian as an approval proxy."""

    async with connect_to_upstream() as upstream_session:
        approval_manager = ApprovalManager()

        loop = asyncio.get_running_loop()

        popup_manager = PopupManager(loop)

        async def handle_list_tools(context, params):
            print(
                "Received tool discovery request.",
                file=sys.stderr,
            )

            return await upstream_session.list_tools(
                params=params,
            )

        async def handle_call_tool(context, params):
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

            try:
                popup_manager.show_popup(
                    request_id=request.request_id,
                    tool_name=request.tool_name,
                    arguments=request.arguments,
                    approval_manager=approval_manager,
                )

                await approval_manager.wait_for_decision(
                    request.request_id,
                    timeout=APPROVAL_TIMEOUT,
                )

                # Approved requests are forwarded.
                if request.status == ApprovalStatus.APPROVED:
                    print(
                        "Request approved. Forwarding upstream.",
                        file=sys.stderr,
                    )

                    try:
                        result = await upstream_session.call_tool(
                            name=params.name,
                            arguments=params.arguments or {},
                        )

                        return result

                    except Exception as error:
                        print(
                            f"Upstream tool execution failed: {error}",
                            file=sys.stderr,
                        )

                        return create_error_result(
                            "MCP Guardian approved the request, but the "
                            "upstream tool failed during execution. "
                            f"Error: {error}"
                        )

                # Explicitly blocked requests.
                if request.status == ApprovalStatus.BLOCKED:
                    reason = request.reason or (
                        "Blocked by user through MCP Guardian."
                    )

                    print(
                        f"Request blocked: {reason}",
                        file=sys.stderr,
                    )

                    return create_error_result(
                        f"Tool execution blocked by MCP Guardian. "
                        f"Reason: {reason}"
                    )

                # Requests that weren't approved in time.
                if request.status == ApprovalStatus.TIMED_OUT:
                    reason = request.reason or (
                        "Approval timed out."
                    )

                    print(
                        f"Request timed out: {reason}",
                        file=sys.stderr,
                    )

                    return create_error_result(
                        f"Tool execution blocked by MCP Guardian. "
                        f"Reason: {reason}"
                    )

                return create_error_result(
                    "Tool execution blocked by MCP Guardian "
                    "because no approval was received."
                )

            except Exception as error:
                print(
                    f"Guardian request error: {error}",
                    file=sys.stderr,
                )

                return create_error_result(
                    "MCP Guardian encountered an internal error "
                    "while processing the approval request."
                )

            finally:
                approval_manager.cleanup_request(
                    request.request_id,
                )

                print(
                    f"Cleaned up request: {request.request_id}",
                    file=sys.stderr,
                )

        guardian = Server(
            "MCP Guardian",
            version="0.1.0",
            on_list_tools=handle_list_tools,
            on_call_tool=handle_call_tool,
        )

        async with stdio_server() as (
            read_stream,
            write_stream,
        ):
            print(
                "MCP Guardian is running.",
                file=sys.stderr,
            )

            await guardian.run(
                read_stream,
                write_stream,
                guardian.create_initialization_options(),
            )


if __name__ == "__main__":
    asyncio.run(main())