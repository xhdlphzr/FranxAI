"""
Agent模块 - AI智能体核心实现
提供EasyMate类，负责与AI模型交互、工具调用和记忆管理
"""

import json
import sys
from pathlib import Path
from openai import OpenAI

# 导入工具系统
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import tools_metadata, tool_functions, readmes_combined

# 用户指南：说明如何正确调用工具
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


class EasyMate:
    """
    AI智能体类
    """

    def __init__(self, key: str, url: str, model: str, settings="你是一个有用的AI助手。", max_iterations=100, temperature=0.8, thinking=False, threshold=20):
        self.client = OpenAI(api_key=key, base_url=url)
        self.model = model
        self.settings = f"{settings}\n\n---\n\n{guide}"
        self.messages = [{"role": "system", "content": self.settings}]
        self.tools = tools_metadata
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.thinking = thinking
        self.threshold = threshold

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
            # 先用流式方式调用，收集文本输出和工具调用增量
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
                    extra_body={
                        "thinking": {
                            "type": "disabled"
                        }
                    }
                )

            # 用于累积完整的响应
            full_content = ""
            tool_calls_data = {}  # 用于累积工具调用，key 为 index

            # 处理流式响应
            for chunk in stream:
                delta = chunk.choices[0].delta

                # 处理文本内容
                if delta.content:
                    full_content += delta.content
                    yield delta.content   # 实时输出

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
                func = tool_functions.get(func_name)
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