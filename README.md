# MCP Guardian

MCP Guardian is a desktop security layer for Model Context Protocol (MCP) tool calls. It intercepts tool requests, displays a user approval popup, and allows users to approve or block each request before it reaches the upstream MCP server.

## Features

- Intercepts MCP tool calls
- Displays an approval popup for every tool invocation
- Approve or block individual requests
- Forwards approved requests to the upstream MCP server
- Blocks execution of denied requests
- Supports concurrent tool requests
- Approval timeout handling
- Automatic popup cleanup
- Integrates with Claude Desktop
- Fail-safe behavior when approval cannot be completed

## Architecture

MCP Guardian acts as an intermediary between Claude Desktop and the upstream MCP server. Tool calls are intercepted and held until the user makes a decision.

```text
Claude Desktop
      |
      v
MCP Guardian Proxy
      |
      v
Approval Manager
      |
      v
Desktop Approval Popup
     / \
 Allow Block
   |     |
   v     v
Upstream  Denied
MCP Server Response
```

### Request Flow

1. Claude Desktop initiates an MCP tool call.
2. MCP Guardian intercepts the request.
3. An approval request is created.
4. A desktop popup displays the tool name and arguments.
5. The user chooses Allow or Block.
6. If approved, the request is forwarded to the upstream MCP server.
7. If blocked, the request is rejected and an error response is returned.
8. The approval request and popup resources are cleaned up.

## Tech Stack

- Python 3.12
- MCP Python SDK
- asyncio
- Tkinter
- pytest
- Claude Desktop
- WSL2 (Windows development environment)

## Project Structure

```text
mcp-guardian/
├── app/
│   ├── approval/
│   │   ├── manager.py
│   │   └── models.py
│   ├── proxy/
│   │   └── mcp_proxy.py
│   ├── ui/
│   │   ├── approval_popup.py
│   │   └── popup_manager.py
│   └── utils/
├── tests/
│   ├── fixtures/
│   │   ├── test_guardian_client.py
│   │   ├── test_mcp_client.py
│   │   └── test_mcp_server.py
│   └── unit/
│       └── test_approval_manager.py
└── README.md
```

## Requirements

- Python 3.12+
- Claude Desktop
- Windows with WSL2 (for the tested development environment)
- A graphical desktop environment capable of displaying Tkinter popups

## Installation

Clone the repository:

```bash
git clone https://github.com/Blackleg-Sanji09/mcp-guardian.git
cd mcp-guardian
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running MCP Guardian

Run the proxy:

```bash
python -m app.proxy.mcp_proxy
```

MCP Guardian starts its upstream MCP server and waits for tool requests.

## Claude Desktop Configuration

Claude Desktop configuration file:

**Windows:**

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Add MCP Guardian under `mcpServers`:

```json
{
  "mcpServers": {
    "mcp-guardian": {
      "command": "wsl",
      "args": [
        "-d",
        "Ubuntu",
        "--",
        "bash",
        "-lc",
        "cd /home/YOUR_USERNAME/mcp-guardian && source .venv/bin/activate && python -m app.proxy.mcp_proxy"
      ]
    }
  }
}
```

Replace `YOUR_USERNAME` with your WSL username and adjust the WSL distribution name if necessary.

Restart Claude Desktop after updating the configuration.

## Testing

Run unit tests:

```bash
pytest -v
```

Run Python compilation checks:

```bash
python -m compileall app tests
```

Run the concurrent integration test:

```bash
python tests/fixtures/test_guardian_client.py
```

The integration test sends two concurrent tool requests and verifies that each can receive an independent approval decision.

## Test MCP Server

The project includes a fixture MCP server with the following tools:

### `calculate_sum`

Calculates the sum of two numbers.

Example arguments:

```json
{
  "a": 10,
  "b": 20
}
```

### `get_system_info`

Returns basic system information, including operating system, release, and architecture.

## Verified Behavior

- Tool discovery
- Approved tool calls forwarded upstream
- Blocked tool calls rejected
- Concurrent requests handled independently
- Approval timeout behavior
- Popup cleanup after decisions and timeout
- Request cleanup
- Claude Desktop integration

## Limitations

- The current implementation is designed and tested for Claude Desktop.
- Claude Web and remote MCP execution are outside the scope of this implementation.
- The included MCP server is a test fixture used for demonstrating the approval workflow.
- Desktop popups require a graphical environment.

## Security Considerations

MCP Guardian provides a user-controlled approval layer before tool execution. Users should review the tool name and arguments displayed in the approval popup before approving a request.

## License

This project is provided as part of a technical assignment.