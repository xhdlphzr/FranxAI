# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Agent Module - Core Implementation of AI Agent | Agent模块 - AI智能体核心实现
Provides the FranxAgent class, responsible for interacting with AI models, tool calling, and memory management | 提供FranxAgent类，负责与AI模型交互、工具调用和记忆管理
"""

import json
import sys
import atexit
import uuid
from pathlib import Path
from openai import OpenAI

# Add project root to path to import the knowledge module | 将项目根目录加入路径，以便导入 skills 模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge import tool_functions, tools_metadata, search, cleanup_mcp_clients

# User guide: explains how to call tools correctly (fixed content, not dependent on knowledge base) | 用户指南：说明如何正确调用工具（固定内容，不依赖知识库）
USER_GUIDE = r"""
## 📌 Tool Calling Convention

**Important: You can only use a tool named `tools`.** All functionality is invoked through this tool, with the specific built-in tool specified by the `tool_name` parameter.

When you decide to use a tool, return the `tools` tool in the standard function-calling format. For example, to get the current time, you should return:

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
- **Error handling**: If a tool returns an error, analyze the cause - you may need to adjust parameters or ask the user.
- **User intent first**: Always choose tools and operations based on the user's request.
- **Do not directly use `time`, `read`, etc. as tool names; they must be called through the `tools` tool.**
- **Use tools, not skills**: Any heading marked with “skill” is not a tool you can call; it is content you should learn.

## 🔨Common Tools
### `read` - Read File Content
- **Purpose**: Call this tool when the user requests to view the content of a file, analyze data within a file, or when you need to obtain information from a file to complete subsequent tasks.
- **Input**:
```json
{
    "path": "Full path of the file"
}
```
    - `path`: **string**, required. The path can be an absolute path, or a relative path based on the current working directory.
- **Output**: File content (text format). An error message will be returned if the file does not exist or cannot be read.
- **Notes**: This tool is read-only and will not modify the file. Ensure the path is correct; confirm the file location via other methods if necessary.

### `write` - Write or append file content
- **Purpose**: Used when the user requests creating new files, writing content to existing files, or modifying files.
- **Input**:
    ```json
    {
        "path": "Full path of the file",
        "content": "Content to write",
        "mode": "overwrite" or "append"  // Default: "overwrite"
    }
    ```
    - `path`: **string**, required, full path of the file
    - `content`: **string**, required, content to be written
    - `mode`: **string**, optional, default is "overwrite". Available values: "overwrite" for replacement, "append" for adding content
- **Output**: Prompt message indicating whether the operation succeeded or failed.
- **Notes**:
    - Ensure the written content is explicitly requested by the user; do not modify files arbitrarily.
    - If the directory where the file is located does not exist, the tool will automatically create the directory (permissions required).

### `command` - Execute System Commands (With Administrator Privileges)
- **Purpose**: Use this tool when users need to run programs, execute scripts, manage system services, install software, or perform other command-line tasks. This tool has **administrator privileges**, enabling most system-level operations.
- **Input**:
```json
{
    "command": "Full command string to execute"
}
```
- `command`: **string** (required; pass the complete system command string)
- **Output**: Standard output and standard error output of the command. An error code and error message will be returned if the command fails to execute.
- **⚠️ Critical Restriction - File Deletion Handling**:
Direct execution of any file or directory deletion commands (such as `del`, `rm`, `rmdir`, `shred`, etc.) with this tool is **strictly prohibited**. If the user requests file deletion, you must:
1. **Do not use the `command` tool to perform deletion operations.**
2. Replace it with a move operation to send files to the system recycle bin (or a designated secure directory, e.g., `C:\Users\Username\To-Delete`). Examples:
    - On Windows: Use `move <file path> <recycle bin path>`. For safe recycling via PowerShell: `Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('<file>','OnlyErrorDialogs','SendToRecycleBin')`. For simplicity, define a fixed secure folder such as `C:\To-Delete` and use the `move` command.
    - On Linux/macOS: Use commands like `mv <file> ~/.Trash/` or `gio trash <file>`.
3. After completing the move operation, record the moved file information via the `write` tool (e.g., write to a log file) for user recovery later.
- **Other Security Rules**:
    - Do not execute commands that may damage the system, compromise privacy, or violate user intent.
    - Never run high-risk operations (e.g., disk formatting, registry modification) regardless of user consent.
    - Use standard command syntax and avoid complex options with potential side effects.

**Usage Principle**: Prioritize safe, compliant commands for user requests. Confirm permissions and risks with users if uncertain. Replace all deletion actions with file moves and record logs strictly.

### `search` - Web Search
- **Purpose**: Search internet information to obtain real-time data, news, encyclopedia content and more.
- **Input**:
    - `query`: **string**, required, search keyword
    - `max_results`: **integer**, optional, number of returned results (default: 5)
- **Output**: Formatted list of search results; each item contains a title, summary and link.
- **Notes**:
    - Completely free, no API Key required.
    - Real-time search results, consistent with DuckDuckGo used in browsers.
    - Please use reasonably, avoid sending a large number of requests in a short period of time.

Now you can start helping the user. Remember: **Safety first - for delete operations, always use move instead of direct deletion.**

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

## 🔨常用工具
### `read` - 读取文件内容
- **用途**：当用户要求查看某个文件的内容、分析文件中的数据、或者你需要从文件中获取信息以完成后续任务时，请调用此工具。
- **输入**：
    ```json
    {
        "path": "文件的完整路径"
    }
    ```
    - `path`：**string**，必填。路径可以是绝对路径，也可以是基于当前工作目录的相对路径。
- **输出**：文件的内容（文本格式）。如果文件不存在或无法读取，会返回错误信息。
- **注意事项**：此工具是只读的，不会修改文件。确保路径正确，必要时可先用其他方式确认文件位置。

### `write` — 写入或追加文件内容
- **用途**：当用户要求创建新文件、向现有文件中写入内容、修改文件时使用。
- **输入**：
    ```json
    {
        "path": "文件的完整路径",
        "content": "要写入的内容",
        "mode": "overwrite" 或 "append"  // 默认 "overwrite"
    }
    ```
    - `path`：**string**，必填，文件的完整路径
    - `content`：**string**，必填，要写入的内容
    - `mode`：**string**，可选，默认为"overwrite"，可选值："overwrite"覆盖、"append"追加
- **输出**：操作成功或失败的提示信息。
- **注意事项**：
  - 请确保写入的内容是用户明确要求的，不要随意修改文件。
  - 如果文件所在目录不存在，工具会自动创建目录（需要权限）。

### `command` - 执行系统命令（具有管理员权限）
- **用途**：当用户需要运行程序、执行脚本、管理系统服务、安装软件等需要命令行操作的任务时，使用此工具。此工具拥有**管理员权限**，因此可以执行大多数系统级操作。
- **输入**：
    ```json
    {
        "command": "要执行的完整命令字符串"
    }
    ```
    - `command`：**string**（必填，需传入完整的系统命令字符串）
- **输出**：命令的标准输出和标准错误输出。如果命令执行失败，会返回错误码和错误信息。
- **⚠️ 重要限制 — 删除文件处理**：
    - 此工具**严禁直接执行任何删除文件或目录的命令**（如 `del`、`rm`、`rmdir`、`shred` 等）。如果用户要求删除文件，你必须：
    1. **不要使用 `command` 工具执行删除操作。**
    2. 改为使用**移动操作**，将文件移动到系统的回收站（或一个指定的安全目录，如 `C:\Users\用户名\待删除`）。例如：
         - 在 Windows 上：使用 `move <文件路径> <回收站路径>` 或 PowerShell 的 `Remove-Item -LiteralPath <文件> -Force` ？不，Remove-Item 会直接删除。更安全的是移动到回收站：你可以使用 PowerShell 命令 `Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('<文件>','OnlyErrorDialogs','SendToRecycleBin')`，但需要谨慎。简单起见，可以定义一个固定的安全目录，例如 `C:\待删除`，然后用 `move` 命令移过去。
         - 在 Linux/macOS 上：可以使用 `mv <文件> ~/.Trash/` 或 `gio trash <文件>` 等命令。
    3. 执行移动操作后，请务必通过 `write` 工具记录下被移动的文件信息（例如写入日志文件），以便用户日后找回。
- **其他安全规则**：
    - 不要执行任何可能损坏系统、危害隐私或违反用户意图的命令。
    - 在执行高危操作（如格式化磁盘、修改注册表等）之前，无论有没有用户同意，都不可以执行。
    - 尽量使用命令的标准语法，避免使用过于复杂或可能产生副作用的选项。

**使用原则**：当用户需求涉及上述命令时，优先选择安全且符合意图的选项。若不确定命令的权限或潜在影响，先向用户确认。对于任何删除类操作，坚决采用移动替代方案，并记录日志。

### search - 网络搜索
- **用途**：搜索互联网信息，获取实时数据、新闻、百科内容等。
- **输入**：
    ```json
    {
        "query": "搜索关键词",
        "max_results": 5
    }
    ```
    - `query`：**string**，必填，搜索关键词
    - `max_results`：**integer**，可选，返回条数（默认 5）
- **输出**：格式化后的搜索结果列表，每条包含标题、摘要、链接。
- **注意事项**：
    - 完全免费，无需 API Key。
    - 搜索结果是实时的，与浏览器中使用 DuckDuckGo 一致。
    - 请合理使用，避免短时间内大量请求。

现在，你可以开始帮助用户了。记住：**安全第一，对于删除操作永远用移动替代直接删除。**
"""

# Summary guide: explains how to summarize conversation content | 摘要指南：说明如何总结对话内容
SUMMARIZE_GUIDE = r"""
Please summarize the following conversation into a concise paragraph (this paragraph will be passed as long‑term memory to a future AI so it can inherit key information). Write in the third person, focusing on:
- The user's core needs or questions
- Confirmed important facts (e.g., file paths, preferences, task status)
- Tools or actions the AI has executed (e.g., which files were read, what commands were run)
- Any pending to-do items

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


class FranxAgent:
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

        # Fixed base system prompt (contains USER_GUIDE and user settings) | 固定的基础系统提示（包含 USER_GUIDE 和用户设置）
        self.base_system_prompt = f"{USER_GUIDE}\n\n---\n\n{self.user_settings}"
        # Persistent message history: first message is always the base system prompt | 持久化消息历史：第一条消息始终是基础系统提示
        self.messages = [{"role": "system", "content": self.base_system_prompt}]

        # Register cleanup of MCP clients on exit | 注册退出时清理 MCP 客户端
        atexit.register(cleanup_mcp_clients)

    def input(self, msg: str):
        """
        Process user messages, supporting streaming output of AI replies | 处理用户消息，支持流式输出 AI 回复
        - Persist user message in history | - 将用户消息持久化到历史
        - Dynamically retrieve knowledge and add as a temporary system message (not persisted) | - 动态检索知识并作为临时系统消息添加（不持久化）
        - When the model returns text, yield it character by character | - 当模型返回文本时，逐字 yield 内容
        - When the model needs to call a tool, execute the tool synchronously and print the tool call info to stdout (can be redirected) | - 当模型需要调用工具时，同步执行工具，并将工具调用信息打印到 stdout（可被重定向）
        - Loop until no tool calls remain | - 循环处理直到无工具调用
        """
        # 1. Persist the current user message | 1. 将当前用户消息持久化
        self.messages.append({"role": "user", "content": msg})

        # 2. Retrieve relevant knowledge for this query | 2. 为本次查询检索相关知识
        relevant = search(msg, k=self.knowledge_k)

        # 3. Build the initial message list for this API call | 3. 构建本次 API 调用的初始消息列表
        # Start with the fixed base system prompt | 以固定的基础系统提示开头
        api_messages = [{"role": "system", "content": self.base_system_prompt}]

        # If there is relevant knowledge, add it as an extra system message (immediately after the base prompt) | 如果有相关知识，添加为额外的系统消息（紧跟在基础提示之后）
        if relevant:
            knowledge_text = "\n\n".join(relevant)
            api_messages.append({
                "role": "system",
                "content": f"## Related Content | 相关内容\n{knowledge_text}"
            })

        api_messages.extend(self.messages[1:])

        # Make a working copy that we will update during the tool call loop | 制作一个工作副本，用于在工具调用循环中更新
        current_api_messages = api_messages.copy()

        iteration = 0
        while iteration < self.max_iterations:
            # Call the model (based on thinking configuration) | 调用模型（根据 thinking 配置）
            if self.thinking:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=current_api_messages,
                    temperature=self.temperature,
                    tools=self.tools,
                    tool_choice="auto",
                    stream=True
                )
            else:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=current_api_messages,
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
            # Append to both current API messages and persistent history | 同时追加到当前 API 消息列表和持久化历史
            current_api_messages.append(assistant_message)
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
                    # Construct new arguments: tool_name is the original function name, arguments are the original parameters | 构造新的 arguments：tool_name 为原函数名，arguments 为原参数
                    new_arguments = {"tool_name": func_name, "arguments": arguments}
                    # Update tool_call object | 更新 tool_call 对象
                    tool_call["function"]["name"] = "tools"
                    tool_call["function"]["arguments"] = json.dumps(new_arguments, ensure_ascii=False)
                    func_name = "tools"
                    arguments = new_arguments

                # Determine the actual tool name | 确定实际的工具名
                actual_tool_name = None
                if func_name == "tools":
                    # Extract tool_name from arguments (when wrapped) | 从参数中提取 tool_name（当包装时）
                    actual_tool_name = arguments.get("tool_name")
                else:
                    actual_tool_name = func_name

                # 1. Send tool_call event first (shows "Using xxx...") | 1. 先发送工具调用事件（显示“Using xxx...”）
                call_id = tool_call["id"]
                yield {
                    "type": "tool_call",
                    "call_id": call_id,
                    "tool_name": actual_tool_name,
                    "arguments": arguments,
                    "result": None # No result yet | 暂无结果
                }

                result = None
                # 2. Check if confirmation is needed | 2. 检查是否需要确认
                if actual_tool_name in ("write", "command"):
                    # Generate a unique confirmation ID | 生成唯一的确认ID
                    confirm_id = str(uuid.uuid4())
                    # 3. Send confirmation request event | 3. 发送确认请求事件
                    approved = yield {
                        "type": "confirmation_required",
                        "confirm_id": confirm_id,
                        "call_id": call_id,
                        "tool_name": actual_tool_name,
                        "arguments": arguments
                    }
                    if approved:
                        # Execute the tool | 执行工具
                        func = self.tool_functions.get(func_name)
                        if func:
                            result = func(**arguments)
                        else:
                            result = f"Error: unknown tool {func_name} | 错误：未知工具 {func_name}"
                    else:
                        # User rejected | 用户拒绝
                        result = f"Tool '{actual_tool_name}' execution was rejected by the user. | 用户拒绝了工具 '{actual_tool_name}' 的执行。"
                else:
                    # Normal execution (no confirmation needed) | 正常执行（无需确认）
                    func = self.tool_functions.get(func_name)
                    if func:
                        result = func(**arguments)
                    else:
                        result = f"Error: unknown tool {func_name} | 错误：未知工具 {func_name}"

                # 4. Send tool result event (updates UI) | 4. 发送工具结果事件（更新界面）
                yield {
                    "type": "tool_result",
                    "call_id": call_id,
                    "result": str(result) if result is not None else "No result | 无结果"
                }

                # Add tool execution result to both current API messages and persistent history | 将工具执行结果同时加入当前 API 消息列表和持久化历史
                tool_message = {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": str(result)
                }
                current_api_messages.append(tool_message)
                self.messages.append(tool_message)

            iteration += 1

        # Max iterations reached | 达到最大迭代次数
        yield "Maximum iterations reached, task may be incomplete. | 已达到最大迭代次数，任务可能未完成。"

    def summarize_msg(self, idx: int):
        """
        Summarize conversation content for memory management, yielding the summary incrementally | 总结对话内容，用于记忆管理，流式输出摘要
        """
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