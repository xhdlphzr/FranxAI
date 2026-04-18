# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Shared State - Global variables and config helpers shared across modules
"""

import json
import threading

# Agent instances (set by init_agents in app.py)
chat_agent = None
chat_agent_lock = threading.Lock()
tasks_agent = None

# Tool confirmation state (shared between /chat and /api/confirm_tool)
pending_confirmations = {}
pending_lock = threading.Lock()

# Cloudflare tunnel URL
public_url = None

def load_config():
    with open("./config.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open("./config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)