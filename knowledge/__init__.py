# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module - Startup Orchestration and Public Exports
"""

from .loader import load_builtin_tools, load_mcp_servers, tool_functions, tools_metadata, cleanup_mcp_clients
from .vector import add_document, check_and_update
from .search import search
from .memory import add_conversation
from .config import VECTOR_DB_PATH, KNOWLEDGE_ROOT

# Startup sequence
load_builtin_tools()
load_mcp_servers()
check_and_update()

# Print status
from .loader import _internal_tools, _mcp_tools
print("Built-in tool list:", list(_internal_tools.keys()))
print(f"MCP tool count: {len(_mcp_tools)}")
print("Knowledge base incremental update completed.")

__all__ = ['tools_metadata', 'tool_functions', 'search', 'cleanup_mcp_clients', 'add_conversation',
           'add_document', 'VECTOR_DB_PATH', 'KNOWLEDGE_ROOT']