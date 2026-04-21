# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module - Built-in Tool Loading, MCP Server Management, Unified Tool Call
"""

import importlib.util
import sys
import json
import time
import threading

from .config import PROJECT_ROOT, TOOLS_DIR
from knowledge.mcps import MCPStdioClient

# Internal tool registry
_internal_tools = {}

# MCP tool registry
_mcp_tools = {}
_mcp_clients = []
_mcp_lock = threading.Lock()


def load_builtin_tools():
    """Load all built-in tools from tools/ directory"""
    global _internal_tools
    _internal_tools = {}
    for item in TOOLS_DIR.iterdir():
        if not item.is_dir() or item.name.startswith('__'):
            continue
        tool_name = item.name
        tool_path = item / 'tool.py'
        readme_path = item / 'README.md'

        if not (tool_path.exists() and readme_path.exists()):
            print(f"⚠️ Tool {tool_name} is missing tool.py or README.md, skipping")
            continue

        try:
            spec = importlib.util.spec_from_file_location(f"knowledge.tools.{tool_name}", tool_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"knowledge.tools.{tool_name}"] = module
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"⚠️ Failed to import tool.py for {tool_name}: {e}, skipping")
            continue

        if not hasattr(module, 'execute'):
            print(f"⚠️ tool.py for {tool_name} does not define execute function, skipping")
            continue

        _internal_tools[tool_name] = module.execute


def load_mcp_servers():
    """Load and start MCP servers from config file"""
    global _mcp_tools
    config_path = PROJECT_ROOT / "config.json"
    if not config_path.exists():
        return
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Failed to read config file: {e}")
        return

    servers = config.get("mcp_servers", [])
    if not servers:
        return

    for server in servers:
        name = server.get("name", "unknown")
        command = server.get("command")
        if not command:
            print(f"Skipping {name}: missing command")
            continue
        args = server.get("args", [])

        try:
            client = MCPStdioClient(command, args)
            client.start()
            time.sleep(0.5)
            raw_tools = client.list_tools()
            if not raw_tools:
                print(f"⚠️ {name} returned no tools, skipping")
                client.close()
                continue

            print(f"Connected to MCP server {name}, found {len(raw_tools)} tools")
            _mcp_clients.append(client)
            with _mcp_lock:
                for tool in raw_tools:
                    tool_name = tool["name"]
                    full_name = f"{name}/{tool_name}"

                    def make_wrapper(mcp_client, t_name):
                        def wrapper(**kwargs):
                            try:
                                return mcp_client.call_tool(t_name, kwargs)
                            except Exception as e:
                                return f"Call failed: {e}"
                        return wrapper
                    _mcp_tools[full_name] = make_wrapper(client, tool_name)
        except Exception as e:
            print(f"Failed to start MCP server {name}: {e}")
            import traceback
            traceback.print_exc()
            continue


def tools(tool_name: str, arguments: dict = None) -> str:
    """
    Unified tool call interface: Supports built-in tools and MCP tools (format: server_name/tool_name)
    """
    if '/' in tool_name:
        with _mcp_lock:
            if tool_name in _mcp_tools:
                try:
                    return _mcp_tools[tool_name](**(arguments or {}))
                except Exception as e:
                    return f"MCP tool call failed: {e}"
            else:
                return f"Error: Unknown MCP tool {tool_name}"
    if tool_name not in _internal_tools:
        return f"Error: Unknown tool {tool_name}"
    try:
        return _internal_tools[tool_name](**(arguments or {}))
    except Exception as e:
        return f"Call failed: {e}"


def cleanup_mcp_clients():
    """Close all MCP clients"""
    for client in _mcp_clients:
        try:
            client.close()
        except:
            pass


# Tool function dictionary
tool_functions = {"tools": tools}

# Tool metadata
tools_metadata = [
    {
        "type": "function",
        "function": {
            "name": "tools",
            "description": "Call any available tool. Parameters: tool_name (tool name), arguments (JSON object). All built-in tools are called through this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Tool name, e.g., read, write, command, search, similarity, add_task, del_task, ett, beijing_subway, etc. External MCP tools use the format server_name/tool_name."
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Tool parameters"
                    }
                },
                "required": ["tool_name"]
            }
        }
    }
]