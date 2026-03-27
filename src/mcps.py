import subprocess
import json
import threading
import time
import sys
from typing import List, Dict, Any

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
        for line in self.process.stdout:
            if line.strip():
                try:
                    data = json.loads(line)
                    with self._lock:
                        self._responses[data["id"]] = data
                except Exception as e:
                    sys.stderr.write(f"解析 MCP 响应失败: {e}, 行: {line}")

    def _send_request(self, method: str, params: Any = None) -> Any:
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
        """发送通知（无需响应）"""
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

    def initialize(self):
        """执行 MCP 初始化握手"""
        params = {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {"name": "FranxAI", "version": "3.0.0"}
        }
        result = self._send_request("initialize", params)
        # 发送 initialized 通知
        self._send_notification("notifications/initialized")
        self._initialized = True
        return result

    def list_tools(self):
        if not self._initialized:
            self.initialize()
        result = self._send_request("tools/list")
        # 处理返回格式：可能直接是数组，也可能是 {"tools": [...]}
        if isinstance(result, dict) and "tools" in result:
            return result["tools"]
        if isinstance(result, list):
            return result
        raise ValueError(f"Unexpected tools/list response: {result}")

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if not self._initialized:
            self.initialize()
        # ---- 参数预处理：将字符串形式的列表/字典转为实际对象 ----
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
        # ---- 预处理结束 ----
        result = self._send_request("tools/call", {"name": name, "arguments": processed})
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False)

    def close(self):
        if self.process:
            self.process.terminate()
            self.process.wait()