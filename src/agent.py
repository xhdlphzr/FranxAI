# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Agent Module - Core Implementation of AI Agent
Provides the FranxAgent class, responsible for interacting with AI models, tool calling, and memory management
"""

import json
import sys
import atexit
import uuid
from pathlib import Path
from openai import OpenAI

# Add project root to path to import the knowledge module
sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge import tool_functions, tools_metadata, search, cleanup_mcp_clients

# User guide: explains how to call tools correctly (fixed content, not dependent on knowledge base)
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
### `read` - Read File Content or Project Structure
- **Purpose**: Call this tool when the user requests to view the content of a file, analyze data within a file, obtain information from a file to complete subsequent tasks, or understand the structure of a project.
- **Input**:
```json
{
    "path": "Full path of the file or directory"
}
```
    - `path`: **string**, required. The path can be an absolute path, or a relative path based on the current working directory. Pass a directory path to scan the project structure.
- **Output**:
    - **Code files** (py, js, ts, rs, go, java, c, cpp, cs, etc.): Returns a `structure` section (AST skeleton with node types, names, and line ranges) followed by a `content` section (full file with line numbers). Use the structure to navigate, and the line numbers to locate exact positions for the `write` tool's edit mode.
    - **Non-code text files**: Returns file content with line numbers.
    - **Document files** (PDF, Word, Excel, PowerPoint, CSV): Returns converted text content.
    - **Image/Video files**: Returns an AI-generated description.
    - **Directory**: Returns a structure map of all code files in the project, showing classes, functions, imports, and their line ranges.
    - An error message will be returned if the path does not exist or cannot be read.
- **Notes**: This tool is read-only and will not modify any files. Ensure the path is correct; confirm the file location via other methods if necessary.

### `write` — Write, append, or edit file content
- **Purpose**: Used when the user requests creating new files, writing content to existing files, or modifying files.
- **Input**:
    ```json
    {
        "path": "Full path of the file",
        "content": "Content to write",
        "mode": "overwrite" or "append" or "edit",
        "start_line": 0,
        "end_line": 0
    }
    ```
    - `path`: **string**, required, full path of the file
    - `content`: **string**, required, content to be written. In edit mode, pass empty string to delete the target lines.
    - `mode`: **string**, optional, default is "overwrite". Available values:
        - `"overwrite"`: Replace entire file
        - `"append"`: Append to end of file
        - `"edit"`: Replace lines from `start_line` to `end_line` (both inclusive, 1-based). Use with `read` tool's line numbers for precise editing.
    - `start_line`: **integer**, required in edit mode. Start line number (1-based, inclusive).
    - `end_line`: **integer**, required in edit mode. End line number (1-based, inclusive).
- **Output**: Prompt message indicating whether the operation succeeded or failed.
- **Notes**:
    - Ensure the written content is explicitly requested by the user; do not modify files arbitrarily.
    - If the directory where the file is located does not exist, the tool will automatically create the directory (permissions required).
    - In edit mode, always use `read` first to get the current line numbers, then specify the exact range to replace.

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

### add_skill - Add a Skill

Add a skill as a Markdown file and immediately indexes it into the knowledge base for real-time retrieval. Use this when you've completed a complex task and want to remember the solution for future use.

**Parameters:**
- `name` (string, required): Skill name, used as filename. Use lowercase with underscores (e.g., "nginx_setup", "python_venv").
- `content` (string, required): Skill content in Markdown format. Should include: title, scenario, step-by-step solution, and notes.

**When to use:**
- After completing a multi-step task that is worth remembering
- When the user asks you to remember something
- When you discover a reusable solution

**When NOT to use:**
- For simple one-off questions
- For information already covered by existing skills

Now you can start helping the user. Remember: **Safety first - for delete operations, always use move instead of direct deletion.**
"""

# Summary guide: explains how to summarize conversation content
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
"""


class FranxAgent:
    """
    AI Agent Class
    """

    def __init__(self, key: str, url: str, model: str,
                 settings="You are a helpful AI assistant.",
                 max_iterations=100,
                 temperature=0.8,
                 thinking=False,
                 knowledge_k=1):
        """
        Initialize the agent
        """
        self.client = OpenAI(api_key=key, base_url=url)
        self.model = model
        self.user_settings = settings
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.thinking = thinking
        self.knowledge_k = knowledge_k   # Number of knowledge fragments to retrieve

        # Unified tool functions (include built-in + MCP)
        self.tool_functions = tool_functions
        self.tools_metadata = tools_metadata
        self.tools = self.tools_metadata

        # Fixed base system prompt (contains USER_GUIDE and user settings)
        self.base_system_prompt = f"{USER_GUIDE}\n\n---\n\n{self.user_settings}"
        # Persistent message history: first message is always the base system prompt
        self.messages = [{"role": "system", "content": self.base_system_prompt}]

        # Register cleanup of MCP clients on exit
        atexit.register(cleanup_mcp_clients)

    def input(self, msg: str):
        """
        Process user messages, supporting streaming output of AI replies
        - Persist user message in history
        - Dynamically retrieve knowledge and add as a temporary system message (not persisted)
        - When the model returns text, yield it character by character
        - When the model needs to call a tool, execute the tool synchronously and print the tool call info to stdout (can be redirected)
        - Loop until no tool calls remain
        """
        # 1. Persist the current user message
        self.messages.append({"role": "user", "content": msg})

        # 2. Retrieve relevant knowledge for this query
        relevant = search(msg, k=self.knowledge_k)

        # 3. Build the initial message list for this API call
        # Start with the fixed base system prompt
        api_messages = [{"role": "system", "content": self.base_system_prompt}]

        # If there is relevant knowledge, add it as an extra system message (immediately after the base prompt)
        if relevant:
            knowledge_text = "\n\n".join(relevant)
            api_messages.append({
                "role": "system",
                "content": f"## Related Content\n\n{knowledge_text}"
            })

        api_messages.extend(self.messages[1:])

        # Make a working copy that we will update during the tool call loop
        current_api_messages = api_messages.copy()

        iteration = 0
        while iteration < self.max_iterations:
            try:
                # Call the model (based on thinking configuration)
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

                full_content = ""      # Accumulate complete response
                tool_calls_data = {}   # Store tool call data

                # Process streaming response
                for chunk in stream:
                    delta = chunk.choices[0].delta

                    # Process text content
                    if delta.content:
                        full_content += delta.content
                        yield delta.content

                    # Process tool calls (incremental)
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_data:
                                # Initialize tool call object
                                tool_calls_data[idx] = {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }
                            if tc.function.name:
                                tool_calls_data[idx]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_data[idx]["function"]["arguments"] += tc.function.arguments

                # Build complete assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": list(tool_calls_data.values()) if tool_calls_data else None
                }
                # Append to both current API messages and persistent history
                current_api_messages.append(assistant_message)
                
                # If no tool calls, finish
                if not tool_calls_data:
                    self.messages.append(assistant_message)
                    return

                # Execute tool calls one by one
                tool_messages = []
                for tool_call in tool_calls_data.values():
                    func_name = tool_call["function"]["name"]
                    
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError as e:
                        # Feed error back to model and continue
                        error_msg = f"JSON parsing error: {e}. Raw arguments: {tool_call['function']['arguments']}"
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": error_msg
                        }
                        tool_messages.append(tool_message)
                        yield {
                            "type": "tool_result",
                            "call_id": tool_call["id"],
                            "result": error_msg
                        }
                        continue

                    # If the model directly called a built-in tool name (e.g., time, read), automatically convert to tools call
                    if func_name != "tools" and "/" not in func_name:
                        # Construct new arguments: tool_name is the original function name, arguments are the original parameters
                        new_arguments = {"tool_name": func_name, "arguments": arguments}
                        # Update tool_call object
                        tool_call["function"]["name"] = "tools"
                        tool_call["function"]["arguments"] = json.dumps(new_arguments, ensure_ascii=False)
                        func_name = "tools"
                        arguments = new_arguments

                    # Determine the actual tool name
                    actual_tool_name = None
                    if func_name == "tools":
                        # Extract tool_name from arguments (when wrapped)
                        actual_tool_name = arguments.get("tool_name")
                    else:
                        actual_tool_name = func_name

                    # 1. Send tool_call event first (shows "Using xxx...")
                    call_id = tool_call["id"]
                    yield {
                        "type": "tool_call",
                        "call_id": call_id,
                        "tool_name": actual_tool_name,
                        "arguments": arguments,
                        "result": None # No result yet
                    }

                    result = None
                    # 2. Check if confirmation is needed
                    if actual_tool_name in ("write", "command"):
                        # Generate a unique confirmation ID
                        confirm_id = str(uuid.uuid4())
                        # 3. Send confirmation request event
                        approved = yield {
                            "type": "confirmation_required",
                            "confirm_id": confirm_id,
                            "call_id": call_id,
                            "tool_name": actual_tool_name,
                            "arguments": arguments
                        }
                        if approved:
                            # Execute the tool
                            func = self.tool_functions.get(func_name)
                            if func:
                                result = func(**arguments)
                            else:
                                result = f"Error: unknown tool {func_name}"
                        else:
                            # User rejected
                            result = f"Tool '{actual_tool_name}' execution was rejected by the user."
                    else:
                        # Normal execution (no confirmation needed)
                        func = self.tool_functions.get(func_name)
                        if func:
                            result = func(**arguments)
                        else:
                            result = f"Error: unknown tool {func_name}"

                    # 4. Send tool result event (updates UI)
                    yield {
                        "type": "tool_result",
                        "call_id": call_id,
                        "result": str(result) if result is not None else "No result"
                    }

                    # Add tool execution result to both current API messages and persistent history
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": str(result)
                    }
                    tool_messages.append(tool_message)

                current_api_messages.extend(tool_messages)
                self.messages.append(assistant_message)
                self.messages.extend(tool_messages)
                iteration += 1
                
            except Exception as e:
                # If API call fails due to context length, compress and retry
                error_str = str(e).lower()
                if "context length" in error_str or "token" in error_str or "too long" in error_str:
                    # Compress messages and retry
                    self.memory()
                    # Rebuild API messages with compressed history
                    current_api_messages = [{"role": "system", "content": self.base_system_prompt}]
                    if relevant:
                        knowledge_text = "\n\n".join(relevant)
                        current_api_messages.append({
                            "role": "system",
                            "content": f"## Related Content\n\n{knowledge_text}"
                        })
                    current_api_messages.extend(self.messages[1:])
                    continue
                else:
                    # Re-raise other exceptions
                    raise

    def summarize_msg(self, idx: int):
        """
        Summarize conversation content for memory management, yielding the summary incrementally
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
        # Update message list: keep system prompt, replace with summary
        self.messages = [self.messages[0]] + [{"role": "system", "content": full_summary}] + self.messages[idx:]

    def memory(self):
        """
        Memory management: automatically compress when context is too long
        """
        if len(self.messages) <= 5:  # Keep at least 5 messages (system + some context)
            return
        # Compress the oldest half of the conversation
        for _ in self.summarize_msg(len(self.messages) // 2 + 1):
            pass