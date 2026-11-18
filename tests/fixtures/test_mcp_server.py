from mcp.server.mcpserver import MCPServer

# Initialize the MCP server
mcp = MCPServer("MCP Guardian Test Server")


@mcp.tool()
def calculate_sum(a: float, b: float) -> float:
    """Calculate the sum of two numbers."""
    return a + b


@mcp.tool()
def get_system_info() -> dict:
    """Return basic information about the current system."""
    import platform

    return {
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
