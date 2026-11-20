import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]


async def main():
    # Launch MCP Guardian as a subprocess.
    guardian_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.proxy.mcp_proxy"],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(guardian_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:

            # Initialize connection with Guardian.
            await session.initialize()

            print("\nConnected to MCP Guardian!")

            # Ask Guardian for available tools.
            tools = await session.list_tools()

            # Test calculate_sum through MCP Guardian.
            result = await session.call_tool(
                "calculate_sum",
                arguments={"a": 10, "b": 20},
            )

            print("\ncalculate_sum result:")
            print(result.content)

            # Test get_system_info through MCP Guardian.
            result = await session.call_tool(
                "get_system_info",
                arguments={},
            )

            print("\nget_system_info result:")
            print(result.content)

            print("\nTools exposed by MCP Guardian:")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())