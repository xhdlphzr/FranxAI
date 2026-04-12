# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

import subprocess
import json
import threading
import time
import sys
from typing import List, Dict, Any

"""
MCP Module - Core Implementation of MCP Server | MCP模块 - MCP服务器核心实现
Provides the MCPStdioClient class to interface with external MCP servers | 提供MCPStdioClient类，以便使用外部MCP服务器
"""

class MCPStdioClient:
    def __init__(self, command: str, args: List[str] = None):
        self.command = command
        self.args = args or []
        self.process = None
        self._request_id = 0
        self._responses = {}
        self._lock = threading.Lock()
        self._reader_thread = None
        self._initialized = False

    def start(self):
        # Start the subprocess and set up pipes | 启动子进程并设置管道
        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )

        def read_stderr():
            for line in self.process.stderr:
                sys.stderr.write(line)
        threading.Thread(target=read_stderr, daemon=True).start()
        self._reader_thread = threading.Thread(target=self._read_responses, daemon=True)
        self._reader_thread.start()

    def _read_responses(self):
        # Read JSON-RPC responses from stdout | 从 stdout 读取 JSON-RPC 响应
        for line in self.process.stdout:
            if line.strip():
                try:
                    data = json.loads(line)
                    with self._lock:
                        self._responses[data["id"]] = data
                except Exception as e:
                    sys.stderr.write(f"Failed to parse MCP response: {e}, line: {line} | 解析 MCP 响应失败: {e}, 行: {line}")

    def _send_request(self, method: str, params: Any = None) -> Any:
        # Send a JSON-RPC request and wait for response | 发送 JSON-RPC 请求并等待响应
        self._request_id += 1
        req_id = self._request_id
        payload = {"jsonrpc": "2.0", "method": method, "id": req_id}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()
        while True:
            with self._lock:
                if req_id in self._responses:
                    resp = self._responses.pop(req_id)
                    if "error" in resp:
                        raise Exception(resp["error"].get("message", "Unknown error"))
                    return resp.get("result")
            time.sleep(0.01)

    def _send_notification(self, method: str, params: Any = None):
        # Send a JSON-RPC notification (no response) | 发送 JSON-RPC 通知（无需响应）
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

    def initialize(self):
        # Perform MCP initialization handshake | 执行 MCP 初始化握手
        params = {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {"name": "FranxAgent", "version": "3.0.0"}
        }
        result = self._send_request("initialize", params)
        # Send initialized notification | 发送 initialized 通知
        self._send_notification("notifications/initialized")
        self._initialized = True
        return result

    def list_tools(self):
        if not self._initialized:
            self.initialize()
        result = self._send_request("tools/list")
        # Handle response format: could be array or {"tools": [...]} | 处理返回格式：可能为数组或 {"tools": [...]}
        if isinstance(result, dict) and "tools" in result:
            return result["tools"]
        if isinstance(result, list):
            return result
        raise ValueError(f"Unexpected tools/list response: {result} | 意外的 tools/list 响应: {result}")

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if not self._initialized:
            self.initialize()
        # Parameter preprocessing: convert string-formatted lists/dicts to actual objects | 参数预处理：将字符串形式的列表/字典转为实际对象
        processed = {}
        for key, value in arguments.items():
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, (list, dict)):
                        processed[key] = parsed
                        continue
                except:
                    pass
            processed[key] = value
        # End preprocessing | 预处理结束
        result = self._send_request("tools/call", {"name": name, "arguments": processed})
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)

    def close(self):
        if self.process:
            self.process.terminate()
            self.process.wait()