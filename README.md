# EasyMate 🤖

**让 AI 像伙伴一样帮你干活，简单、安全、低成本。**

EasyMate 是一个轻量级的 AI 智能体框架，基于大模型（如 Ollama、OpenAI、GLM 等）和工具调用，让 AI 能够真正操作你的电脑——读取文件、写入内容、执行命令、查询时间、搜索网络、计算文本相似度、定时执行任务、甚至看懂图片和文档……所有操作都受控且安全，无需复杂的配置。

---

## ✨ 核心特性

- 🛠️ 丰富的内置工具：`time`、`read`、`write`、`command`、`search`、`similarity`、`add_task`、`del_task`、`ett（多模态理解）`、`beijing_subway（北京地铁换乘）`等，支持自由扩展
- 🧠 **智能记忆**：自动压缩历史对话，生成长期记忆，跨会话保留用户偏好与重要信息
- ⏰ **定时任务**：后台线程运行，支持每天重复任务，让 AI 在指定时间自动执行指令
- 🔒 **安全第一**：`command` 工具禁止直接删除文件，自动提示改用移动操作，高风险操作可配置审批
- 🕸️ **免费网络搜索**：集成 DuckDuckGo，无需 API Key，即搜即用
- 📊 **文本相似度计算**：基于滚动哈希，快速判断字符串相似度
- 🖼️ **多模态理解**：支持图片、视频、文档（Word、Excel、PDF 等）分析，让 AI 真正看懂世界
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
如果是 windows 打开 `start.bat`，macOS 打开 `start.sh` 即可自动完成。

### 3. 配置
复制 `config.example.json` 并改名为 `config.json`，然后根据你的需求修改。

在 `config.json` 中，你可以根据需要调整以下参数：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `api_key` | string | - | API 密钥（必填）。Ollama 可填任意值。 |
| `base_url` | string | - | API 基础地址（必填）。例如 Ollama 为 `http://localhost:11434/v1`，GLM 为 `https://open.bigmodel.cn/api/paas/v4`。 |
| `model` | string | - | 模型名称（必填）。推荐 `glm-4.7-flash`、`qwen2.5:7b` 等。 |
| `settings` | string | `"你是一个有用的AI助手。"` | 系统提示词，用于设定 AI 的角色或行为规则。 |
| `temperature` | float | `0.8` | 生成随机性，取值范围 0~1。值越低回答越确定，越高越有创意。 |
| `thinking` | bool | `false` | 是否启用深度思考模式（仅对 GLM 模型有效）。开启后模型会输出推理过程，但响应稍慢。 |
| `max_iterations` | int | `100` | 工具调用的最大循环次数，防止无限循环。 |
| `threshold` | int | `20` | 触发历史压缩的消息数量阈值。当对话消息超过此值时，会自动将最早的 10 条压缩成摘要。 |

**多模态工具独立配置（可选）**  
在 `tools` 字段中可为 `ett`（多模态理解）单独指定参数，若不设置则自动使用顶层配置：

```json
{
    "tools": {
        "ett": {
            "api_key": "your-ett-api-key",          // 可选，不填则使用顶层 api_key
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4.6v-flash",               // 推荐视觉模型
            "temperature": 0.8,
            "thinking": false,
            "max_retries": 5                        // API 限流重试次数
        }
    }
}
```

> ⚠️ **注意**：多模态工具 `ett` 目前仅支持智谱 GLM 系列模型（如 `glm-4.6v-flash`），使用前请确保配置了正确的 API 密钥和模型名称。

**示例配置（使用智谱 GLM）**：
```json
{
    "api_key": "your-zhipu-api-key",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "model": "glm-4.7-flash",
    "temperature": 0.8,
    "thinking": false,
    "max_iterations": 100,
    "threshold": 20,
    "settings": "你是一个有用的AI助手。",
    "tools": {
        "ett": {
            "api_key": "your-zhipu-api-key",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4.6v-flash",
            "max_retries": 5
        }
    }
}
```

> 💡 **小贴士**：修改配置后保存，新配置将在下一次对话时自动生效，无需重启服务。

> 💡 **模型推荐**：推荐 `glm-4.7-flash` 作为对话模型，`glm-4.6v-flash` 作为视觉模型，两者配合使用效果最佳。

### 4. 运行
如果是 windows 打开 `run.bat`，macOS 打开 `run.sh` 即可。结束的时候在终端按 `Ctrl+C` 退出。

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
| `ett` | 多模态理解 | 分析图片、视频、文档（Word/Excel/PDF）等，返回文字描述。依赖智谱 GLM-4.6V-Flash，支持公网 URL 或本地文件（自动转 base64）。 |
| `beijing_subway` | 北京地铁换乘规划 | 输入起点和终点站名，返回最优换乘方案（考虑早晚高峰速度）。需将 `station.json` 和 `graph.txt` 放入 `tools/beijing_subway/` 目录，并安装 `geopy` 库。 |

**说明**：
- 所有工具均已集成到 EasyMate 的工具系统中，AI 会根据用户指令自动调用。
- `command` 工具已内置安全拦截，禁止直接执行删除类命令。
- `similarity` 可用于比较文本相似度，适用于去重、查重等场景。
- 定时任务功能由后台线程支持，每天重复执行，无需用户持续在线。
- `ett` 工具目前仅支持智谱 GLM 系列模型，使用时请确保 `tools.ett` 配置正确。

---

## 🧠 记忆与定时任务

- **长期记忆**：每次对话结束后，AI 会自动生成全局摘要并存入 `memory.txt`，下次启动时加载，实现跨会话记忆。
- **历史压缩**：当对话超过 `threshold` 条时，自动将前一半对话压缩成摘要，保持上下文不超限。
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

```
用户：
这张图里有什么？https://example.com/dog.jpg
AI：调用 ett 工具分析图片，返回描述。
```

```
用户：
帮我分析这个 Word 文档的内容（提供本地路径）
AI：调用 ett 工具处理文档，返回文字摘要。
```

---

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request！请确保代码风格清晰，并更新相关文档。

---

## 📄 许可证

[GPL v3](COPYING)

---

## 🙏 致谢

- 所有使用和支持 EasyMate 的朋友
- [MateUnion](https://github.com/MateUnion)——人众帮团队，欢迎关注！
- [xhdlphzr](https://github.com/xhdlphzr)——一个忙碌的码农
- [zhiziwj](https://github.com/zhiziwj)——提出了一个建议，虽然没有实现，不过很有价值，同时实现了一个功能
- [humanity687](https://github.com/humanity687)——提出了几个很有建设性的问题，已经一一研究修复