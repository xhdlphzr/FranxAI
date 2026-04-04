# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
Agent Module - Core Implementation of AI Agent | Agent模块 - AI智能体核心实现
Provides the FranxAI class, responsible for interacting with AI models, tool calling, and memory management | 提供FranxAI类，负责与AI模型交互、工具调用和记忆管理
"""

import json
import sys
import atexit
from pathlib import Path
from openai import OpenAI

# Add project root to path to import the knowledge module | 将项目根目录加入路径，以便导入 skills 模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge import tool_functions, tools_metadata, search, cleanup_mcp_clients

# User guide: explains how to call tools correctly (fixed content, not dependent on knowledge base) | 用户指南：说明如何正确调用工具（固定内容，不依赖知识库）
USER_GUIDE = r"""
## 📌 Tool Calling Convention

**Important: You can only use a tool named `tools`.** All functionality is invoked through this tool, with the specific built‑in tool specified by the `tool_name` parameter.

When you decide to use a tool, return the `tools` tool in the standard function‑calling format. For example, to get the current time, you should return:

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

For tools that require parameters, `arguments` must be a JSON object containing all required fields. For example, to read a file:

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

## 🧠 Tool Usage Principles
- **Least privilege**: Only use the tools necessary to complete the task; do not misuse `command` for file operations (use `read`/`write` instead).
- **Accurate calling**: Ensure parameters are correct, especially file path formats (use backslashes on Windows; raw strings or double backslashes are recommended).
- **Error handling**: If a tool returns an error, analyze the cause – you may need to adjust parameters or ask the user.
- **User intent first**: Always choose tools and operations based on the user’s request.
- **Do not directly use `time`, `read`, etc. as tool names; they must be called through the `tools` tool.**
- **Use tools, not skills**: Any heading marked with “skill” is not a tool you can call; it is content you should learn.

Now you can start helping the user. Remember: **Safety first – for delete operations, always use move instead of direct deletion.**

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
- **使用工具而非技能，注意任何一个标题后标了技能的都是不能使用的，而是你要学习的**

现在，你可以开始帮助用户了。记住：**安全第一，对于删除操作永远用移动替代直接删除。**
"""

# Summary guide: explains how to summarize conversation content | 摘要指南：说明如何总结对话内容
SUMMARIZE_GUIDE = r"""
Please summarize the following conversation into a concise paragraph (this paragraph will be passed as long‑term memory to a future AI so it can inherit key information). Write in the third person, focusing on:
- The user’s core needs or questions
- Confirmed important facts (e.g., file paths, preferences, task status)
- Tools or actions the AI has executed (e.g., which files were read, what commands were run)
- Any pending to‑do items

Requirements:
- The summary must be based solely on the provided conversation; do not add any extra content.
- Keep the language concise, within 150 words.
- Ignore pleasantries, repetitions, and irrelevant details.
- If certain information is missing, omit it.

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
    AI Agent Class | AI智能体类
    """

    def __init__(self, key: str, url: str, model: str,
                 settings="You are a helpful AI assistant. 你是一个有用的AI助手。。",
                 max_iterations=100,
                 temperature=0.8,
                 thinking=False,
                 threshold=20,
                 knowledge_k=1):
        """
        Initialize the agent | 初始化智能体
        """
        self.client = OpenAI(api_key=key, base_url=url)
        self.model = model
        self.user_settings = settings
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.thinking = thinking
        self.threshold = threshold
        self.knowledge_k = knowledge_k   # Number of knowledge fragments to retrieve | 检索知识数量

        # Unified tool functions (include built-in + MCP) | 统一工具函数（已包含内置 + MCP）
        self.tool_functions = tool_functions
        self.tools_metadata = tools_metadata
        self.tools = self.tools_metadata

        # Base system prompt (without dynamic knowledge) | 基础系统提示（不含动态知识）
        base_prompt = f"{USER_GUIDE}\n\n---\n\n{self.user_settings}"
        self.base_messages = [{"role": "system", "content": base_prompt}]

        # Actual message history (copies base_messages and is enhanced before each conversation) | 实际消息历史（会复制 base_messages 并在每次对话前增强）
        self.messages = self.base_messages.copy()

        # Register cleanup of MCP clients on exit | 注册退出时清理 MCP 客户端
        atexit.register(cleanup_mcp_clients)

    def _build_enhanced_system_prompt(self, user_input):
        """
        Retrieve relevant knowledge based on user input and return an enhanced system prompt string | 根据用户输入检索相关知识，并返回增强后的系统提示字符串
        """
        # Retrieve relevant knowledge | 检索相关知识
        relevant = search(user_input, k=self.knowledge_k)
        if not relevant:
            return self.base_messages[0]["content"]

        knowledge_text = "\n\n".join(relevant)
        return self.base_messages[0]["content"] + f"\n\n## Related Content | 相关内容\n{knowledge_text}"

    def input(self, msg: str):
        """
        Process user messages, supporting streaming output of AI replies | 处理用户消息，支持流式输出 AI 回复
        - Dynamically retrieve knowledge and enhance the system prompt before each conversation | - 每次对话前动态检索知识并增强系统提示
        - When the model returns text, yield it character by character | - 当模型返回文本时，逐字 yield 内容
        - When the model needs to call a tool, execute the tool synchronously and print the tool call info to stdout (can be redirected) | - 当模型需要调用工具时，同步执行工具，并将工具调用信息打印到 stdout（可被重定向）
        - Loop until no tool calls remain | - 循环处理直到无工具调用
        """
        print("AI is thinking... | AI思考中...")

        # Build the enhanced message list for this conversation | 为本次对话构建增强后的消息列表
        enhanced_system = self._build_enhanced_system_prompt(msg)
        self.messages = [{"role": "system", "content": enhanced_system}] + self.base_messages[1:]
        self.messages.append({"role": "user", "content": msg})

        iteration = 0
        while iteration < self.max_iterations:
            # Call the model (based on thinking configuration) | 调用模型（根据 thinking 配置）
            if self.thinking:
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

            full_content = ""      # Accumulate complete response | 累积完整的响应
            tool_calls_data = {}   # Store tool call data | 存储工具调用数据

            # Process streaming response | 处理流式响应
            for chunk in stream:
                delta = chunk.choices[0].delta

                # Process text content | 处理文本内容
                if delta.content:
                    full_content += delta.content
                    yield delta.content

                # Process tool calls (incremental) | 处理工具调用（增量）
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_data:
                            # Initialize tool call object | 初始化工具调用对象
                            tool_calls_data[idx] = {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        if tc.function.name:
                            tool_calls_data[idx]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_data[idx]["function"]["arguments"] += tc.function.arguments

            # Build complete assistant message | 构建完整的 assistant 消息
            assistant_message = {
                "role": "assistant",
                "content": full_content,
                "tool_calls": list(tool_calls_data.values()) if tool_calls_data else None
            }
            self.messages.append(assistant_message)

            # If no tool calls, finish | 如果没有工具调用，结束
            if not tool_calls_data:
                return

            # Execute tool calls one by one | 有工具调用，逐个执行
            for tool_call in tool_calls_data.values():
                func_name = tool_call["function"]["name"]
                arguments = json.loads(tool_call["function"]["arguments"])

                # If the model directly called a built-in tool name (e.g., time, read), automatically convert to tools call | 如果模型直接调用了内置工具名（如 time、read），自动转换为 tools 调用
                if func_name != "tools" and "/" not in func_name:
                    print(f"⚠️ The model directly called {func_name}, automatically converting to tools call | ⚠️ 模型直接调用了 {func_name}，已自动转换为 tools 调用")
                    # Construct new arguments: tool_name is the original function name, arguments are the original parameters | 构造新的 arguments：tool_name 为原函数名，arguments 为原参数
                    new_arguments = {"tool_name": func_name, "arguments": arguments}
                    # Update tool_call object | 更新 tool_call 对象
                    tool_call["function"]["name"] = "tools"
                    tool_call["function"]["arguments"] = json.dumps(new_arguments, ensure_ascii=False)
                    func_name = "tools"
                    arguments = new_arguments

                # Get the tool function | 获取工具函数
                func = self.tool_functions.get(func_name)

                if func:
                    result = func(**arguments)
                    print(f"Using tool {func_name} with arguments {arguments}, result: \"{result}\" | 使用工具 {func_name}，参数 {arguments}，调用结果 “{result}”")
                else:
                    result = f"Error: unknown tool {func_name} | 错误：未知工具 {func_name}"
                    print(result)

                # Add tool execution result to message history | 将工具执行结果加入消息历史
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(result)
                })

            iteration += 1

        # Max iterations reached | 达到最大迭代次数
        yield "Maximum iterations reached, task may be incomplete. | 已达到最大迭代次数，任务可能未完成。"

    def summarize_msg(self, idx: int):
        """
        Summarize conversation content for memory management, yielding the summary incrementally | 总结对话内容，用于记忆管理，流式输出摘要
        """
        print("AI is summarizing... | AI概括中...")
        to_summarize = self.messages[1:idx]
        to_summarize.append({"role": "user", "content": SUMMARIZE_GUIDE})
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
        # Update message list: keep system prompt, replace with summary | 更新消息列表：保留系统提示，替换为摘要
        self.messages = [self.messages[0]] + [{"role": "system", "content": full_summary}] + self.messages[idx:]

    def memory(self):
        """
        Memory management: automatically compress when the message count exceeds the threshold | 记忆管理：当消息超过阈值时，自动压缩
        """
        if len(self.messages) <= self.threshold:
            return
        # Consume the summary generator to complete compression (ignore output) | 消费摘要生成器，完成压缩（忽略输出）
        for _ in self.summarize_msg(len(self.messages) // 2 + 1):
            pass 