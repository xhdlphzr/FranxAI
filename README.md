# FranxAI 🤖

**Let AI work like a partner – simple, safe, low cost.**

FranxAI is a lightweight AI agent framework that enables AI to read files, execute commands, search the web, understand multimodal content, and truly control the world through the MCP protocol. **Now, it also features an "Echo of Thought" vector knowledge base: all tool descriptions, skill files, and even conversation history are automatically vectorized and persistently stored. With every query, the AI retrieves the most relevant knowledge fragments and injects them into the system prompt, enabling long-term memory, cross-session recall, and dynamic knowledge enhancement. From "Words to Worlds", now let every echo nourish thought.**

---

## ✨ Core Features

- 🛠️ **Rich built‑in tools**: `time`, `read`, `write`, `command`, `search`, `similarity`, `ett` (multimodal understanding), `beijing_subway` (Beijing subway route planning), etc. Easily extensible.
- 🌐 **MCP protocol support**: Integrate any stdio‑based MCP server with simple configuration (command + args). The AI automatically learns to use all its tools.
- 🧠 **Intelligent memory**: Automatically compresses conversation history and stores complete dialogues into `knowledge/memories/`, which are reloaded on next startup for cross‑session knowledge retrieval.
- ⏰ **Scheduled tasks**: Background thread runs daily repeated tasks; the AI executes instructions at specified times.
- 📚 **Skill system**: All Markdown files under `knowledge/` are automatically merged into the system prompt, injecting domain knowledge, rules, or workflows.
- 🔒 **Safety first**: The `command` tool prohibits direct file deletion; suggests moving instead. High‑risk operations can be configured for approval.
- 🕸️ **Free web search**: Built‑in DuckDuckGo search – no API key required.
- 📊 **Text similarity**: Rolling‑hash based similarity calculation for strings.
- 🖼️ **Multimodal understanding**: Supports images, videos, documents (Word, Excel, PDF). The AI truly sees the world.
- ⚙️ **Minimal configuration**: Single `config.json` for API key, model, system prompt.
- 📦 **Lightweight dependencies**: Only Python standard library + `openai` SDK (compatible with local Ollama and various cloud APIs).
- 💻 **Cross‑platform**: Path handling via `pathlib` works on Windows, Linux, macOS.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/xhdlphzr/FranxAI.git
cd FranxAI
```

### 2. Create virtual environment and install dependencies
Windows users: double‑click `start.bat`; macOS users: double‑click `start.sh`.

### 3. Configuration
Copy `config.example.json` to `config.json` and edit.

Available fields in `config.json`:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `api_key` | string | - | API key (required). For Ollama, any value works. |
| `base_url` | string | - | API base URL (required). e.g. `http://localhost:11434/v1` for Ollama, `https://open.bigmodel.cn/api/paas/v4` for GLM. |
| `model` | string | - | Model name (required). Recommended: `glm-4.7-flash`, `qwen2.5:7b`. |
| `settings` | string | `"You are a helpful AI assistant. 你是一个有用的AI助手。"` | System prompt to set AI role/behavior. |
| `temperature` | float | `0.8` | Randomness (0‑1). Lower = more deterministic. |
| `thinking` | bool | `false` | Enable deep‑thinking mode (GLM only). Slower but outputs reasoning. |
| `max_iterations` | int | `100` | Max tool call iterations to prevent infinite loops. |
| `threshold` | int | `20` | When message count exceeds this, compress the earliest 10 into a summary. |
| `knowledge_k` | int | `1` | Number of knowledge fragments retrieved per conversation. Larger values inject more context but consume more tokens. |
| `mcp_servers` | list | `[]` | MCP server configurations, each with `name`, `command`, `args` (optional). Example: `[{"name": "windows-mcp", "command": "uvx", "args": ["windows-mcp"]}]`. |

**Independent ETT (multimodal) configuration (optional)**  
You can specify separate parameters for `ett` under the `tools` field:

```json
{
    "tools": {
        "ett": {
            "api_key": "your-ett-api-key",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4.6v-flash",
            "temperature": 0.8,
            "thinking": false,
            "max_retries": 5
        }
    }
}
```

> ⚠️ **Note**: The `ett` tool currently only supports Zhipu GLM series models (e.g. `glm-4.6v-flash`). Make sure to configure the correct API key and model.

**Example configuration (Zhipu GLM + Windows‑MCP)**:
```json
{
    "api_key": "your-zhipu-api-key",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "model": "glm-4.7-flash",
    "temperature": 0.8,
    "thinking": false,
    "max_iterations": 100,
    "threshold": 20,
    "knowledge_k": 3,
    "settings": "You are a helpful AI assistant.",
    "tools": {
        "ett": {
            "api_key": "your-zhipu-api-key",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "model": "glm-4.6v-flash",
            "temperature": 0.8,
            "thinking": false,
            "max_iterations": 100,
            "max_retries": 20
        }
    },
    "mcp_servers": [
        {
            "name": "windows-mcp",
            "command": "uvx",
            "args": ["windows-mcp"]
        }
    ]
}
```

> 💡 **Tip**: After saving configuration changes, they take effect in the next conversation – no need to restart.

> 💡 **Model recommendation**: Use `glm-4.7-flash` for conversation and `glm-4.6v-flash` for vision tasks.

### 4. Run
Windows: double‑click `run.bat`; macOS: double‑click `run.sh`. Press `Ctrl+C` to exit.

Ask a question, and the AI will use tools to help you.

---

## 🛠️ Tool Descriptions

| Tool | Purpose | Security / Notes |
|------|---------|------------------|
| `time` | Current date/time | Read‑only, safe |
| `read` | Read file content | Read‑only |
| `write` | Write/append to file | Auto‑creates parent directories; overwrite/append options |
| `command` | Execute system command | ❌ Direct deletion blocked; suggests moving instead. Supports timeout. |
| `search` | Web search (DuckDuckGo) | Free, no API key. Returns title, snippet, URL. |
| `similarity` | String similarity (rolling hash) | Window size 3 bytes, returns percentage. |
| `add_task` | Add scheduled task | Parameters: `content`, `time` (HH:MM) |
| `del_task` | Delete scheduled task | Delete by ID, auto‑renumber remaining tasks |
| `ett` | Multimodal understanding | Analyze images, videos, documents (Word/Excel/PDF). Requires Zhipu GLM‑4.6V‑Flash. Supports public URL or local file (auto base64). |
| `beijing_subway` | Beijing subway route planning | Input start and end station names, returns optimal route (peak/off‑peak speed considered). Requires `station.json` and `graph.txt` in `knowledge/tools/beijing_subway/` and `geopy` installed. |

**MCP tool integration**  
Add any MCP server (stdio mode) in `config.json`:
```json
{
    "mcp_servers": [
        {
            "name": "windows-mcp",
            "command": "uvx",
            "args": ["windows-mcp"]
        }
    ]
}
```
After startup, the AI automatically discovers all tools from these servers and calls them via the unified `tools` tool. No extra configuration – just say “take a screenshot”.

**Remote hardware (e.g., Raspberry Pi)**  
To control remote hardware via SSH, add a configuration like:
```json
{
  "mcp_servers": [
    {
      "name": "raspberry-gpio",
      "command": "ssh",
      "args": ["-T", "pi@raspberry-ip", "python", "/home/pi/raspberry_mcp.py"]
    }
  ]
}
```

**Notes**:
- All tools (built‑in + MCP) are called via the single `tools` tool, saving tokens.
- Built‑in tool names are fixed (e.g., `read`, `write`). MCP tools use `server/tool` format (e.g., `windows-mcp/snapshot`).
- `command` has built‑in safety; deleting requires moving.
- `similarity` helps with deduplication and checking.
- Scheduled tasks run in background, daily repetition, no persistent user online required.
- `ett` only supports Zhipu GLM models; ensure correct `tools.ett` configuration.

---

## 🧠 Skill System

FranxAI loads Markdown files from `knowledge/skills/` and merges them into the system prompt. You can write `.md` files to inject domain knowledge, behavior rules, workflows, etc., customizing the AI's behavior.

**Usage**:
1. Create `skills/` under `knowledge/` if not exists.
2. Place your Markdown files there (e.g., `coding_style.md`, `company_rules.md`). You can copy some skills from the [skills branch](https://github.com/xhdlphzr/FranxAI/tree/skills) (note: these skills undergo some review, but FranxAI is not responsible for their content).
3. Start FranxAI – all `.md` files are automatically read, sorted by filename, and appended after `settings` in the system prompt.

**Example**:
Suppose `skills/coding_style.md` contains:
> Code style: Use 4‑space indentation, snake_case for variables, camelCase for functions.

The AI will then follow these style conventions in subsequent conversations.

> ⚠️ **Disclaimer**: Skill files are provided by users; FranxAI assumes no responsibility for their content. Ensure the content complies with laws and does not contain sensitive or harmful information.

---

## 🧠 Memory & Scheduled Tasks

- **Long‑term memory**: FranxAI no longer relies on `memory.txt`. Complete conversation history is automatically saved to `knowledge/memories/` (one `.md` file per session). On next startup, these histories are loaded into the vector knowledge base, allowing semantic retrieval of past conversations.
- **History compression**: When messages exceed `threshold`, the first half is compressed into a summary to keep context within limits.
- **Scheduled tasks**: Background thread checks `tasks.json` every 10 seconds; executes commands at specified times (HH:MM). Supports daily repetition without duplication.

---

## 🧪 Usage Examples

User:
```
List files in the current directory
```
AI: Calls `tools(tool_name="command", arguments={"command": "ls"})` and returns the list.

User:
```
Remind me to drink a glass of water every morning at 8am
```
AI: Calls `tools(tool_name="add_task", arguments={"content": "Remind me to drink water", "time": "08:00"})`, task added.

User:
```
Compute the similarity between "hello world" and "hello word"
```
AI: Calls `tools(tool_name="similarity", arguments={"text1": "hello world", "text2": "hello word"})`, returns 33.33%.

User:
```
Search for Python asynchronous programming
```
AI: Calls `tools(tool_name="search", arguments={"query": "Python asynchronous programming"})`, returns results.

User:
```
What is in this picture? https://example.com/dog.jpg
```
AI: Calls `tools(tool_name="ett", arguments={"url": "https://example.com/dog.jpg", "prompt": "What is in this picture?", "type": "image_url"})`, returns description.

User:
```
Analyze the content of this Word document (local path provided)
```
AI: Calls `tools(tool_name="ett", arguments={"url": "C:/docs/report.docx", "prompt": "Analyze this document", "type": "file_url"})`, returns summary.

User:
```
(After configuring Windows‑MCP) Take a screenshot
```
AI: Calls `tools(tool_name="windows-mcp/snapshot")`, returns screenshot result.

---

## 🤝 Contributing

Issues and Pull Requests are welcome! Please keep code clear and update relevant documentation.

---

## 📄 License

[GPL v3](COPYING)

---

## 🙏 Acknowledgements

- All friends who use and support FranxAI
- [xhdlphzr](https://github.com/xhdlphzr) – a busy coder
- [zhiziwj](https://github.com/zhiziwj) – provided a suggestion that, while not implemented, was valuable; also implemented a feature
- [humanity687](https://github.com/humanity687) – raised several constructive issues, all addressed