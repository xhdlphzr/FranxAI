import json
import tools
from openai import OpenAI

guide = r"""
你拥有以下四个工具，可以帮助你完成用户的任务。当你需要获取信息或对系统进行操作时，请选择合适的工具，并按要求的格式调用。**永远不要猜测或假设数据，始终通过工具获取真实信息。**

---

### 1. `time` — 获取当前日期和时间
- **用途**：当你需要知道当前的日期、时间、星期几，或者计算时间间隔时使用。
- **输入**：不需要任何参数。
- **输出**：返回一个字符串，包含当前的本地日期和时间（例如：`2026-03-14 星期六 15:30:45`）。
- **注意事项**：此工具只是读取系统时钟，不会修改任何内容。

### 2. `read` — 读取文件内容
- **用途**：当用户要求查看某个文件的内容、分析文件中的数据、或者你需要从文件中获取信息以完成后续任务时，请调用此工具。
- **输入**：
  ```json
  {
    "path": "文件的完整路径"
  }
  ```
  路径可以是绝对路径，也可以是基于当前工作目录的相对路径。
- **输出**：文件的内容（文本格式）。如果文件不存在或无法读取，会返回错误信息。
- **注意事项**：此工具是只读的，不会修改文件。确保路径正确，必要时可先用其他方式确认文件位置。

### 3. `write` — 写入或追加文件内容
- **用途**：当用户要求创建新文件、向现有文件中写入内容、修改文件时使用。
- **输入**：
  ```json
  {
    "path": "文件的完整路径",
    "content": "要写入的内容",
    "mode": "overwrite" 或 "append"  // 默认 "overwrite"
  }
  ```
  - `mode` 可选：`"overwrite"` 覆盖已有内容，`"append"` 追加到文件末尾。
- **输出**：操作成功或失败的提示信息。
- **注意事项**：
  - 请确保写入的内容是用户明确要求的，不要随意修改文件。
  - 如果文件所在目录不存在，工具会自动创建目录（需要权限）。

### 4. `command` — 执行系统命令（具有管理员权限）
- **用途**：当用户需要运行程序、执行脚本、管理系统服务、安装软件等需要命令行操作的任务时，使用此工具。此工具拥有**管理员权限**，因此可以执行大多数系统级操作。
- **输入**：
  ```json
  {
    "command": "要执行的完整命令字符串"
  }
  ```
- **输出**：命令的标准输出和标准错误输出。如果命令执行失败，会返回错误码和错误信息。
- **⚠️ 重要限制 — 删除文件处理**：
  此工具**严禁直接执行任何删除文件或目录的命令**（如 `del`、`rm`、`rmdir`、`shred` 等）。如果用户要求删除文件，你必须：
  1. **不要使用 `command` 工具执行删除操作。**
  2. 改为使用**移动操作**，将文件移动到系统的回收站（或一个指定的安全目录，如 `C:\Users\用户名\待删除`）。例如：
     - 在 Windows 上：使用 `move <文件路径> <回收站路径>` 或 PowerShell 的 `Remove-Item -LiteralPath <文件> -Force` ？不，Remove-Item 会直接删除。更安全的是移动到回收站：你可以使用 PowerShell 命令 `Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('<文件>','OnlyErrorDialogs','SendToRecycleBin')`，但需要谨慎。简单起见，可以定义一个固定的安全目录，例如 `C:\待删除`，然后用 `move` 命令移过去。
     - 在 Linux/macOS 上：可以使用 `mv <文件> ~/.Trash/` 或 `gio trash <文件>` 等命令。
  3. 执行移动操作后，请务必通过 `write` 工具记录下被移动的文件信息（例如写入日志文件），以便用户日后找回。
- **其他安全规则**：
  - 不要执行任何可能损坏系统、危害隐私或违反用户意图的命令。
  - 在执行高危操作（如格式化磁盘、修改注册表等）之前，如果没有用户明确且具体的指令，请先与用户确认。
  - 尽量使用命令的标准语法，避免使用过于复杂或可能产生副作用的选项。

---

## 📌 工具调用方式
当你决定使用某个工具时，请以标准的函数调用格式返回。例如，如果你要获取时间，你应该返回：
```json
{
  "tool_calls": [{
    "id": "call_unique_id",
    "type": "function",
    "function": {
      "name": "time",
      "arguments": "{}"
    }
  }]
}
```
对于需要参数的工具，`arguments` 必须是一个包含所有必需字段的 JSON 字符串，例如：
```json
{
  "tool_calls": [{
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "read",
      "arguments": "{\"path\": \"C:\\Users\\Example\\document.txt\"}"
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

现在，你可以开始帮助用户了。记住：**安全第一，对于删除操作永远用移动替代直接删除。**
"""

class EasyMate:
    def __init__(self, key: str, url: str, model: str, settings="你是一个有用的AI助手。"):
        self.client = OpenAI(
            api_key=key,
            base_url=url
        )
        self.model = model
        self.settings = f"{guide}\n\n{settings}"
        self.messages = [{"role": "system", "content": f"{guide} \n {settings}"}]
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "time",
                    "description": "获取当前本地日期和时间，例如 'YYYY-MM-DD 星期X HH:MM:SS'。不需要任何参数。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read",
                    "description": "读取指定文件的内容。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件的完整路径，可以是绝对路径或相对于当前工作目录的路径。"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write",
                    "description": "写入或追加内容到文件。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "文件的完整路径。"
                            },
                            "content": {
                                "type": "string",
                                "description": "要写入的内容。"
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["overwrite", "append"],
                                "description": "写入模式：'overwrite' 覆盖，'append' 追加。默认为 'overwrite'。"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "command",
                    "description": "执行一条系统命令（具有管理员权限）。注意：严禁直接执行删除命令，如需删除文件请改用移动操作。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "要执行的完整命令字符串。"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    def input(self, msg: str) -> str:
        self.messages.append({"role": "user", "content": msg})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools,
            tool_choice="auto"
        )
        message = response.choices[0].message
        self.messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                if func_name == "time":
                    result = tools.get_time()
                elif func_name == "read":
                    result = tools.read_file(**arguments)
                elif func_name == "write":
                    result = tools.write_file(**arguments)
                elif func_name == "command":
                    result = tools.execute_command(**arguments)
                else:
                    result = f"未知工具：{func_name}"

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            final_answer = final_response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": final_answer})
        else:
            final_answer = message.content
            self.messages.append({"role": "assistant", "content": final_answer})

        return final_answer