# EasyMate 🤖

**让 AI 像伙伴一样帮你干活，简单、安全、低成本。**

EasyMate 是一个轻量级的 AI 智能体框架，基于大模型（如 Ollama、OpenAI 等）和工具调用，让 AI 能够真正操作你的电脑——读取文件、写入内容、执行命令、查询时间……所有操作都受控且安全，无需复杂的配置。

## ✨ 核心特性

- 🛠️ **内置四个实用工具**：`time`（时间查询）、`read`（读文件）、`write`（写文件）、`command`（执行命令）
- 🔒 **安全第一**：禁止直接删除文件（自动建议移动操作），所有高风险操作均可配置审批
- 🧠 **智能自主**：AI 自动拆解任务，按需调用工具，多步协作
- ⚙️ **极简配置**：一个 `config.json` 文件搞定 API 密钥、模型选择
- 📦 **无外部依赖**：仅需 Python 标准库 + `openai` SDK（兼容 Ollama）
- 🪶 **超低 token 消耗**：轻量设计，适合本地部署

## 🚀 快速开始

### 1. 复制并下载

仅需从github上复制并下载requirements.txt依赖仅可

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

### 4. 运行
```bash
python main.py
```
输入你的问题，AI 就会调用工具帮你完成。

## 📁 项目结构
```
EasyMate/
├── main.py              # 程序入口（支持多行输入）
├── agent.py             # EasyMate 核心类（对话管理、工具调用循环）
├── tools.py             # 四个工具的具体实现
├── config.json          # 用户配置文件（需自行创建）
├── config.example.json  # 配置文件模板
└── README.md
```

## 🛠️ 工具说明
| 工具 | 作用 | 安全限制 |
|------|------|----------|
| `time` | 获取当前日期时间 | 只读，无风险 |
| `read` | 读取文件内容 | 只读，仅返回文件内容 |
| `write` | 写入/追加文件 | 自动创建父目录，不会覆盖已有文件（除非指定 `overwrite`） |
| `command` | 执行系统命令 | ❌ 禁止直接删除文件（自动提示改用移动操作）；支持超时控制 |

## 🧪 使用示例
```
用户（空行结束）：
帮我看看当前目录有哪些文件

AI：调用 command 执行 ls（或 dir），返回目录列表。
```

## 🤝 贡献指南
欢迎提交 Issue 或 Pull Request！请确保代码风格清晰，并更新相关文档。

## 📄 许可证
[MIT](LICENSE)

## 🙏 致谢
- 所有使用和支持 EasyMate 的朋友
- xhdlphzr