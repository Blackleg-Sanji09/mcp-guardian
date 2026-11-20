import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["tests/fixtures/test_mcp_server.py"],
    )

    async with stdio_client(server_params) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            # Initialize the MCP connection
            await session.initialize()

            print("Connected to MCP server!")

            # Discover available tools
            tools = await session.list_tools()

            print("\nAvailable tools:")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            # Invoke calculate_sum
            result = await session.call_tool(
                "calculate_sum",
                arguments={"a": 10, "b": 20},
            )

            print("\ncalculate_sum result:")
            print(result.content)

            # Invoke get_system_info
            result = await session.call_tool(
                "get_system_info",
                arguments={},
            )

            print("\nget_system_info result:")
            print(result.content)


if __name__ == "__main__":
    asyncio.run(main())