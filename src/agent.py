# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
Agent模块 - AI智能体核心实现
提供FranxAI类，负责与AI模型交互、工具调用和记忆管理
"""

import json
import sys
import atexit
import time
import threading
from pathlib import Path
from openai import OpenAI
from mcps import MCPStdioClient

# 导入工具系统
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import tools_metadata, tool_functions, readmes_combined
from tools import tools as builtin_tools

# 用户指南：说明如何正确调用工具
user_guide = r"""
## 📌 工具调用方式

**重要：你只能使用一个名为 `tools` 的工具。** 所有功能都通过这个工具调用，具体调用哪个内置工具由 `tool_name` 参数指定。

当你决定使用某个工具时，请以标准的函数调用格式返回 `tools` 工具。例如，如果你要获取时间，你应该返回：

```json
{
  "tool_calls": [{
    "id": "call_unique_id",
    "type": "function",
    "function": {
      "name": "tools",
      "arguments": "{\"tool_name\": \"time\", \"arguments\": {}}"
    }
  }]
}
```

对于需要参数的工具，`arguments` 必须是一个包含所有必需字段的 JSON 对象。例如，读取文件：

```json
{
  "tool_calls": [{
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "tools",
      "arguments": "{\"tool_name\": \"read\", \"arguments\": {\"path\": \"C:\\\\Users\\\\Example\\\\document.txt\"}}"
    }
  }]
}
```

---

## 🧠 工具使用原则
- **最小权限**：只使用完成任务所必需的工具，不要滥用 `command` 做文件读写（应该用 `read`/`write`）。
- **准确调用**：确保参数正确，特别是文件路径的格式（Windows 路径使用反斜杠，建议用原始字符串或双反斜杠）。
- **错误处理**：如果工具返回错误，请分析原因，可能需要调整参数或询问用户。
- **用户意图优先**：始终围绕用户的请求来选择工具和操作方式。
- **禁止直接使用 `time`、`read` 等作为工具名，必须通过 `tools` 工具调用。**

现在，你可以开始帮助用户了。记住：**安全第一，对于删除操作永远用移动替代直接删除。**
"""

# 将工具的README和用户指南合并
guide = f"{readmes_combined}\n\n---\n\n{user_guide}"

# 摘要指南：说明如何总结对话内容
summarize_guide = r"""
请将以下对话内容总结为一个简洁的段落（这个段落将作为长期记忆传递给未来的AI，让它继承关键信息）。请用第三人称叙述，重点保留：
- 用户的核心需求或问题
- 已确认的重要事实（如文件路径、偏好设置、任务状态）
- AI 已执行的工具或操作（如读取了哪些文件、运行了什么命令）
- 任何尚未完成的待办事项

要求：
- 摘要必须仅基于提供的对话，不要添加任何额外内容。
- 语言简洁，控制在150字以内。
- 忽略寒暄、重复或无关细节。
- 如果某项信息缺失，则省略。
"""


class FranxAI:
    """
    AI智能体类
    """

    def __init__(self, key: str, url: str, model: str, settings="你是一个有用的AI助手。", max_iterations=100, temperature=0.8, thinking=False, threshold=20):
        self.client = OpenAI(api_key=key, base_url=url)
        self.model = model
        self.user_settings = settings
        self.user_guide = user_guide

        self.builtin_tools = builtin_tools

        # 存储 MCP 工具的函数映射（键为 "服务器名/工具名"）
        self.mcp_tools = {}
        # 存储 MCP 工具的描述（用于系统提示）
        self.mcp_descriptions = []

        # 定义统一的 tools 函数，先尝试内置，再尝试 MCP
        def wrapped_tools(tool_name: str, arguments: dict = None) -> str:
            tool_name = tool_name.strip()  # 只去除首尾空格，保留原始大小写
            if '/' in tool_name:
                # 精确匹配
                if tool_name in self.mcp_tools:
                    try:
                        return self.mcp_tools[tool_name](**(arguments or {}))
                    except Exception as e:
                        return f"调用 MCP 工具失败: {e}"
                # 大小写不敏感匹配
                for key in self.mcp_tools:
                    if key.lower() == tool_name.lower():
                        try:
                            return self.mcp_tools[key](**(arguments or {}))
                        except Exception as e:
                            return f"调用 MCP 工具失败: {e}"
                return f"错误：未知 MCP 工具 {tool_name}。可用的 MCP 工具: {list(self.mcp_tools.keys())}"
            
            # 调用内置工具
            try:
                return self.builtin_tools(tool_name, arguments)
            except Exception as e:
                return f"调用内置工具失败: {e}"

        self.tool_functions = {"tools": wrapped_tools}
        self.tools_metadata = tools_metadata   # 只有一个工具定义
        self.tools = self.tools_metadata

        # 构建系统提示（基础部分）
        base_prompt = f"{readmes_combined}\n\n---\n\n{self.user_guide}\n\n---\n\n{self.user_settings}"
        self.messages = [{"role": "system", "content": base_prompt}]

        # 其他属性
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.thinking = thinking
        self.threshold = threshold

        # MCP 客户端管理
        self._mcp_lock = threading.Lock()
        self.mcp_clients = []
        self._mcp_clients_map = {}

        # 加载 MCP 服务器
        self._load_mcp_servers()

        # 更新系统提示（加入 MCP 描述和调用说明）
        self._update_system_prompt()

        # 退出清理
        atexit.register(self._cleanup_mcp_clients)

    def _load_mcp_servers(self):
        """从配置文件加载 MCP 服务器并启动，注册工具函数和描述"""
        config_path = Path(__file__).parent.parent / "config.json"
        if not config_path.exists():
            return
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return

        servers = config.get("mcp_servers", [])
        if not servers:
            return

        for server in servers:
            name = server.get("name", "unknown")
            command = server.get("command")
            if not command:
                print(f"跳过 {name}: 缺少 command")
                continue
            args = server.get("args", [])

            try:
                client = MCPStdioClient(command, args)
                client.start()
                time.sleep(0.5)
                raw_tools = client.list_tools()
                if not raw_tools:
                    print(f"⚠️ {name} 未返回工具，跳过")
                    client.close()
                    continue

                print(f"已连接 MCP 服务器 {name}，发现 {len(raw_tools)} 个工具")
                self._mcp_clients_map[name] = client
                with self._mcp_lock:
                    for tool in raw_tools:
                        tool_name = tool["name"]
                        full_name = f"{name}/{tool_name}"   # 服务器名/工具名
                        description = tool.get("description", "")
                        # 生成自然语言描述
                        desc = description
                        params = tool.get("inputSchema", {}).get("properties", {})
                        param_str = ", ".join([f"{k} ({v.get('type','any')})" for k, v in params.items()])
                        if param_str:
                            desc += f" 参数：{param_str}。"
                        self.mcp_descriptions.append(f"- {full_name}：{desc}")

                        # 创建包装函数
                        def make_wrapper(mcp_client, t_name):
                            def wrapper(**kwargs):
                                try:
                                    return mcp_client.call_tool(t_name, kwargs)
                                except Exception as e:
                                    return f"调用失败: {e}"
                            return wrapper
                        self.mcp_tools[full_name] = make_wrapper(client, tool_name)

                self.mcp_clients.append(client)
            except Exception as e:
                print(f"启动 MCP 服务器 {name} 失败: {e}")
                import traceback
                traceback.print_exc()
                continue

    def _update_system_prompt(self):
        """将 MCP 工具描述和调用说明追加到系统提示"""
        current = self.messages[0]["content"]
        if self.mcp_descriptions:
            current += "\n\n## 外部 MCP 工具\n" + "\n".join(self.mcp_descriptions)
        current += "\n\n## 调用方式\n所有工具都通过 `tools` 工具调用，格式为 `tools(tool_name=\"工具名\", arguments={...})`。内置工具使用原始名称（如 read），外部 MCP 工具使用 `服务器名/工具名`（如 windows-mcp/snapshot）。"
        self.messages[0]["content"] = current

    def _cleanup_mcp_clients(self):
        for client in self.mcp_clients:
            try:
                client.close()
            except:
                pass

    def input(self, msg: str):
        """
        处理用户消息，支持流式输出 AI 回复。
        - 当模型返回文本时，逐字 yield 内容。
        - 当模型需要调用工具时，同步执行工具，并将工具调用信息打印到 stdout（可被重定向）。
        - 循环处理直到无工具调用。
        """
        print("AI思考中...")
        self.messages.append({"role": "user", "content": msg})

        iteration = 0
        while iteration < self.max_iterations:
            # 调用模型（根据 thinking 配置）
            if self.thinking == True:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature,
                    tools=self.tools,
                    tool_choice="auto",
                    stream=True
                )
            else:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=self.temperature,
                    tools=self.tools,
                    tool_choice="auto",
                    stream=True,
                    extra_body={"thinking": {"type": "disabled"}}
                )

            # 用于累积完整的响应
            full_content = ""
            tool_calls_data = {}

            # 处理流式响应
            for chunk in stream:
                delta = chunk.choices[0].delta

                # 处理文本内容
                if delta.content:
                    full_content += delta.content
                    yield delta.content

                # 处理工具调用（增量）
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            # 初始化工具调用对象
                            tool_calls_data[idx] = {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        if tc.function.name:
                            tool_calls_data[idx]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_data[idx]["function"]["arguments"] += tc.function.arguments

            # 构建完整的 assistant 消息
            assistant_message = {
                "role": "assistant",
                "content": full_content,
                "tool_calls": list(tool_calls_data.values()) if tool_calls_data else None
            }
            self.messages.append(assistant_message)

            # 如果没有工具调用，结束
            if not tool_calls_data:
                return

            # 有工具调用，逐个执行
            for tool_call in tool_calls_data.values():
                func_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])
                
                # 如果模型直接调用了内置工具名（如 time、read），自动转换为 tools 调用
                if func_name != "tools" and "/" not in func_name:
                    print(f"⚠️ 模型直接调用了 {func_name}，已自动转换为 tools 调用")
                    # 构造新的 arguments：tool_name 为原函数名，arguments 为原参数
                    new_arguments = {"tool_name": func_name, "arguments": arguments}
                    # 更新 tool_call 对象
                    tool_call["function"]["name"] = "tools"
                    tool_call["function"]["arguments"] = json.dumps(new_arguments, ensure_ascii=False)
                    func_name = "tools"  # 后续使用新名称
                    arguments = new_arguments   # 后续使用新参数
                
                func = self.tool_functions.get(func_name)

                if func:
                    result = func(**arguments)
                    print(f"使用工具 {func_name}，参数 {arguments}，调用结果 “{result}”")
                else:
                    result = f"错误：未知工具 {func_name}"
                    print(result)
                # 将工具执行结果加入消息历史
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(result)
                })

            iteration += 1

        # 达到最大迭代次数
        yield "已达到最大迭代次数，任务可能未完成。"

    def summarize_msg(self, idx: int):
        """
        总结对话内容，用于记忆管理，流式输出摘要。
        """
        print("AI概括中...")
        to_summarize = self.messages[1:idx]
        to_summarize.append({"role": "user", "content": summarize_guide})
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=to_summarize,
            stream=True
        )
        full_summary = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_summary += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content
        # 更新消息列表
        self.messages = [self.messages[0]] + [{"role": "system", "content": full_summary}] + self.messages[idx:]

    def memory(self):
        """
        记忆管理：当消息超过阈值时，自动压缩。
        """
        if len(self.messages) <= self.threshold:
            return
        # 消费摘要生成器，完成压缩（忽略输出）
        for _ in self.summarize_msg(len(self.messages) // 2 + 1):
            pass