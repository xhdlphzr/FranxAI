import json
import sys
from pathlib import Path
from openai import OpenAI
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import tools_metadata, tool_functions, readmes_combined

user_guide = r"""
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
guide = f"{readmes_combined}\n\n---\n\n{user_guide}"

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

class EasyMate:
    def __init__(self, key: str, url: str, model: str, settings="你是一个有用的AI助手。"):
        self.client = OpenAI(
            api_key=key,
            base_url=url
        )
        self.model = model
        self.settings = f"{guide}\n\n{settings}"
        self.messages = [{"role": "system", "content": self.settings}]
        self.tools = tools_metadata

    def input(self, msg: str) -> str:
        max_iterations=100
        self.messages.append({"role": "user", "content": msg})
        print("AI思考中...")

        iteration = 0
        while iteration < max_iterations:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto"
            )
            message = response.choices[0].message
            self.messages.append(message.model_dump())

            if not message.tool_calls:
                return message.content

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                func = tool_functions.get(func_name)

                if func:
                    result = func(**arguments)
                    print(f"使用工具{func_name}，调用参数{arguments}，正在进行中...")
                else:
                    result = f"错误：未知工具{func_name}"
                    print(result)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })

            if len(message.tool_calls) > 1:
                print("⚠️ 模型返回了多个工具调用，将按顺序逐个执行，请稍候...")

            iteration += 1

        return "已达到最大迭代次数，任务可能未完成。"
    
    def summarize_msg(self, idx: int) -> str:
        summarize = self.messages[1:idx]
        summarize.append({"role": "user", "content": summarize_guide})
        
        print("AI概括中...")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=summarize
        )

        self.messages = [self.messages[0]] + [{"role": "system", "content": response.choices[0].message.content}] + self.messages[idx:]
        return response.choices[0].message.content
    
    def memory(self, max_iterations=20):
        if self.messages.__len__() <= max_iterations:
            return
        
        self.summarize_msg(11)

    def msgs(self) -> str:
        return self.messages