# EasyMate 🤖

**让 AI 像伙伴一样帮你干活，简单、安全、低成本。**

EasyMate 是一个轻量级的 AI 智能体框架，基于大模型（如 Ollama、OpenAI、GLM 等）和工具调用，让 AI 能够真正操作你的电脑——读取文件、写入内容、执行命令、查询时间、搜索网络、计算文本相似度、定时执行任务……所有操作都受控且安全，无需复杂的配置。

---

## ✨ 核心特性

- 🛠️ **丰富的内置工具**：`time`、`read`、`write`、`command`、`search`、`similarity`、`add_task`、`del_task` 等，支持自由扩展
- 🧠 **智能记忆**：自动压缩历史对话，生成长期记忆，跨会话保留用户偏好与重要信息
- ⏰ **定时任务**：后台线程运行，支持每天重复任务，让 AI 在指定时间自动执行指令
- 🔒 **安全第一**：`command` 工具禁止直接删除文件，自动提示改用移动操作，高风险操作可配置审批
- 🕸️ **免费网络搜索**：集成 DuckDuckGo，无需 API Key，即搜即用
- 📊 **文本相似度计算**：基于滚动哈希，快速判断字符串相似度
- ⚙️ **极简配置**：一个 `config.json` 搞定 API 密钥、模型选择、系统提示
- 📦 **轻量依赖**：仅需 Python 标准库 + `openai` SDK（兼容本地 Ollama 及各类云端 API）
- 💻 **跨平台兼容**：代码使用 `pathlib` 处理路径，可在 Windows / Linux / macOS 上运行

---

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/MateUnion/EasyMate.git
cd EasyMate
```

### 2. 创建虚拟环境并安装依赖
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# 或 .\venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 3. 配置
复制配置文件模板并修改：
```bash
cp config.example.json config.json
```
编辑 `config.json`，填入你的 API 信息（Ollama 可填任意 key）：
```json
{
  "api_key": "your-api-key",
  "base_url": "http://localhost:11434/v1",
  "model": "qwen2.5:7b",
  "settings": "你是一个有用的AI助手。"
}
```

> 💡 **模型推荐**：推荐 `glm-4.7-flash` 模型，比较聪明，弱智AI发挥不出实力

### 4. 运行
```bash
python src/main.py
```
输入你的问题，AI 就会调用工具帮你完成。

---

## 🛠️ 工具说明

| 工具 | 作用 | 安全限制 / 备注 |
|------|------|------------------|
| `time` | 获取当前日期时间 | 只读，无风险 |
| `read` | 读取文件内容 | 只读，仅返回文件内容 |
| `write` | 写入/追加文件 | 自动创建父目录，覆盖/追加可选 |
| `command` | 执行系统命令 | ❌ 禁止直接删除文件（自动提示改用移动操作）；支持超时控制 |
| `search` | 网络搜索（DuckDuckGo） | 免费，无需 API Key，返回标题、摘要、链接 |
| `similarity` | 计算两个字符串的相似度 | 基于滚动哈希，窗口大小固定为 3 字节，返回百分比 |
| `add_task` | 添加定时任务 | 参数：`content`（任务描述）、`time`（格式 `HH:MM`） |
| `del_task` | 删除定时任务 | 按 ID 删除，自动重排剩余任务 ID |

**说明**：
- 所有工具均已集成到 EasyMate 的工具系统中，AI 会根据用户指令自动调用。
- `command` 工具已内置安全拦截，禁止直接执行删除类命令。
- `similarity` 可用于比较文本相似度，适用于去重、查重等场景。
- 定时任务功能由后台线程支持，每天重复执行，无需用户持续在线。

---

## 🧠 记忆与定时任务

- **长期记忆**：每次对话结束后，AI 会自动生成全局摘要并存入 `memory.txt`，下次启动时加载，实现跨会话记忆。
- **历史压缩**：当对话超过 20 条时，自动将最早的 10 条对话压缩成摘要，保持上下文不超限。
- **定时任务**：后台线程每 10 秒检查 `tasks.json`，到达指定时间（如 `14:30`）时执行对应指令，支持每天重复，不会重复执行。

---

## 🧪 使用示例

```
用户（c结束）：
帮我看看当前目录有哪些文件
c
AI：调用 command 执行 ls（或 dir），返回目录列表。
```

```
用户：
每天早上 8 点提醒我喝一杯水
AI：已添加任务，每天 08:00 将执行“提醒我喝一杯水”。
```

```
用户：
计算字符串 "hello world" 和 "hello word" 的相似度
AI：调用 similarity 返回相似度百分比。
```

```
用户：
搜索 Python 异步编程
AI：调用 search 返回相关结果。
```

---

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request！请确保代码风格清晰，并更新相关文档。

---

## 📄 许可证

[MIT](LICENSE)

---

## 🙏 致谢

- 所有使用和支持 EasyMate 的朋友
- [MateUnion](https://github.com/MateUnion)——人众帮团队，欢迎关注！
- [xhdlphzr](https://github.com/xhdlphzr)——一个忙碌的码农
- [zhiziwj](https://github.com/zhiziwj)——提出了一个建议，虽然没有实现，不过很有价值，同时实现了一个功能
- [humanity687](https://github.com/humanity687)——提出了几个很有建设性的问题，已经一一研究修复