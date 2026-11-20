import asyncio
import sys
import os
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
        env={
            **os.environ,
            "DISPLAY": os.environ.get("DISPLAY", ":0"),
            "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY", "wayland-0"),
        },
    )

    async with stdio_client(guardian_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:

            # Initialize connection with Guardian.
            await session.initialize()

            print("\nConnected to MCP Guardian!")

            # Ask Guardian for available tools.
            tools = await session.list_tools()

            print("\nSending two tool requests concurrently...")

            # Request 1
            async def request_one():
                return await session.call_tool(
                    "calculate_sum",
                    arguments={"a": 10, "b": 20},
                )

            # Request 2
            async def request_two():
                return await session.call_tool(
                    "calculate_sum",
                    arguments={"a": 5, "b": 7},
                )

            # Send both requests at the same time.
            results = await asyncio.gather(
                request_one(),
                request_two(),
            )

            print("\nRequest 1: calculate_sum(10, 20)")
            print("Result:", results[0].content)

            print("\nRequest 2: calculate_sum(5, 7)")
            print("Result:", results[1].content)

            print("\nTools exposed by MCP Guardian:")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())