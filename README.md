# FranxAgent 🤖

**English** | [中文](docs/README_zh.md)

**Let AI work for you like a partner – simple, secure, low cost.**  
**Now you can control the AI on your computer directly from your phone – no public IP, no port forwarding, one‑click secure remote access.**

FranxAgent is a lightweight AI agent framework that enables AI to read files, execute commands, search the web, understand multimodal content, and truly interact with the world through the MCP protocol.  
**Now it also features:**
- 🌐 **One‑click intranet penetration**: integrated Cloudflare Tunnel – start it and get a public URL, access from your phone or tablet anytime, anywhere.
- 🔐 **Military‑grade security authentication**: RSA public‑key encryption + JWT short‑lived tokens, supports “refresh‑to‑re‑login” mode, completely eliminating long‑term token leakage risks.
- 📱 **Perfect mobile adaptation**: bottom liquid‑glass dock, breathing dot animation, touch optimisation – same experience on phone and desktop.
- 🧠 **Echoes of Thoughts knowledge base**: all tool descriptions, skill files, and conversation histories are automatically vectorised, using hybrid search (vector semantics + keyword matching) for long‑term memory and cross‑session recall.

**From now on, AI can not only go “From Words to Worlds”, but also “let every echo become the nourishment of thought”.**

---

## ✨ Core Features

- 📱 **Zero‑configuration remote access**: integrated Cloudflare Tunnel – one‑click public URL, no public IP or router settings needed. Access FranxAgent on your computer directly from your phone/tablet.
- 🔐 **Military‑grade security authentication**: RSA asymmetric encryption + JWT short‑lived tokens, supports “refresh‑to‑re‑login” (token stored only in memory, cleared on page refresh), completely prevents long‑term control after token leakage.
- 🧠 **Intelligent memory & hybrid search**: conversation history automatically stored in vector database, combined with FTS5 keyword search for precise cross‑session recall.
- 🛠️ **Rich built‑in tools**: `time`, `read`, `write`, `command`, `search`, `similarity`, `ett` (multimodal understanding), `beijing_subway`, etc., extensible.
- 🌐 **MCP protocol support**: integrate any stdio MCP server with a simple configuration – AI automatically learns to use all its tools.
- ⏰ **Scheduled tasks**: runs in background thread, supports daily recurring tasks – AI executes commands at specified times.
- 📚 **Skill system**: Markdown files in `knowledge/` are automatically merged into the system prompt, giving AI extra knowledge, rules, or workflows.
- 🔒 **Security first**: `command` tool prohibits direct file deletion, suggests moving instead; high‑risk operations can require approval.
- 🕸️ **Free web search**: DuckDuckGo integration, no API key needed.
- 🖼️ **Multimodal understanding**: analyse images, videos, documents (Word, Excel, PDF, etc.).
- ⚙️ **Minimal configuration**: one `config.json` handles all settings.
- 📦 **Lightweight dependencies**: Minimalist dependency.
- 💻 **Cross‑platform**: Windows / Linux / macOS.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/xhdlphzr/FranxAgent.git
cd FranxAgent
```

### 2. Install dependencies
Windows users double‑click `init.bat`, macOS users double‑click `init.sh` – virtual environment and dependencies will be set up automatically.

### 3. Configure
Modify `config.json` according to your needs (see configuration section below).

### 4. Run
Windows users double‑click `run.bat`, macOS users double‑click `run.sh`.  
After startup, the terminal will display a public URL (e.g. `https://xxxx.trycloudflare.com`). **Open that link on your phone browser** – the first time you will be guided to set a password, then log in and control the AI on your computer from your phone.

> 💡 **Security tip**: JWT tokens are valid for only 1 hour and are stored only in browser memory – they are lost on page refresh. Do not use remote access on public computers.

### 5. Use
Type your question in the chat box – the AI will automatically call tools to help you. The mobile experience is identical to the desktop version, with touch, swipe, and voice input support (via the phone’s own input methods).

---

## ⚠️ Disclaimer

The Cloudflare Tunnel remote access feature provided by FranxAgent is offered as a technical convenience. Users assume all risks associated with network exposure, device loss, password leakage, third‑party attacks, or any other cause that may lead to damage to devices, data, or personal safety. Before use, ensure that:
- You set a strong password and change it regularly;
- You enable remote access only on trusted networks and devices;
- You understand and accept that any networked service may have unknown security vulnerabilities.

The project authors and contributors accept no liability for any direct or indirect losses arising from the use of this software. **By using this software, you indicate that you have read and agreed to this disclaimer.**

---

## ⚙️ Configuration

In `config.json`, you can adjust the following parameters:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | string | `"en"` | Language for UI and system prompt. |
| `api_key` | string | - | API key (required). For Ollama, any value works. |
| `base_url` | string | - | API base URL (required). For Ollama: `http://localhost:11434/v1`, for GLM: `https://open.bigmodel.cn/api/paas/v4`. |
| `model` | string | - | Model name (required). Recommended: `glm-4.7-flash`, `qwen2.5:7b`, etc. |
| `settings` | string | `"You are a helpful AI assistant."` | System prompt defining AI’s role or behaviour. |
| `temperature` | float | `0.8` | Randomness, range 0–2 (but recommended 0–1). Lower = more deterministic, higher = more creative. |
| `thinking` | bool | `false` | Enable deep thinking mode (GLM models only). The model outputs reasoning steps but responds slightly slower. |
| `max_iterations` | int | `100` | Max tool call iterations to prevent infinite loops. |
| `threshold` | int | `20` | Message count threshold for history compression. When exceeded, the oldest 10 messages are summarised. |
| `knowledge_k` | int | `5` | Number of knowledge snippets retrieved per conversation for knowledge‑augmented prompts. Larger values inject more system prompt but may bring more relevant info. |
| `mcp_servers` | list | `[]` | List of MCP server configurations, each with `name`, `command`, `args` (optional). Example: `[{"name": "windows-mcp", "command": "uvx", "args": ["windows-mcp"]}]`. |

**Multimodal tool independent configuration (optional)**  
Inside the `tools` field, you can specify separate parameters for `ett` (multimodal understanding). If not set, the top‑level configuration is used:

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

> ⚠️ **Note**: The multimodal tool `ett` currently only supports GLM series models (e.g. `glm-4.6v-flash`). Ensure you have configured the correct API key and model name.

**Example configuration (using GLM + Windows‑MCP)**:
```json
{
    "language": "en",
    "api_key": "your-zhipu-api-key",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "model": "glm-4.7-flash",
    "temperature": 0.8,
    "thinking": false,
    "max_iterations": 100,
    "threshold": 20,
    "knowledge_k": 5,
    "settings": "You are a helpful AI assistant.",
    "tools": {
        "ett": {
            "api_key": "your-zhipu-api-key",
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

> 💡 **Tip**: After saving configuration changes, they take effect in the next conversation – no need to restart the service.

> 💡 **Model recommendation**: Use `glm-4.7-flash` for conversation and `glm-4.6v-flash` for vision tasks.

---

## 🛠️ Tool Descriptions

| Tool | Purpose | Security / Notes |
|------|---------|------------------|
| `time` | Current date/time | Read‑only, safe |
| `read` | Read file content | Read‑only, returns file content |
| `write` | Write/append to file | Auto‑creates parent directories; overwrite/append options |
| `command` | Execute system command | ❌ Direct deletion blocked; suggests moving instead. Supports timeout. |
| `search` | Web search (DuckDuckGo) | Free, no API key. Returns title, snippet, URL. |
| `similarity` | String similarity (rolling hash) | Window size 3 bytes, returns percentage. |
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

FranxAgent loads Markdown files from `knowledge/skills/` and merges them into the system prompt. You can write `.md` files to inject domain knowledge, behavior rules, workflows, etc., customising the AI's behaviour.

**Usage**:
1. Create `skills/` under `knowledge/` if not exists.
2. Place your Markdown files there (e.g., `coding_style.md`, `company_rules.md`). You can copy some skills from the [skills branch](https://github.com/xhdlphzr/FranxAgent/tree/skills) (note: these skills undergo some review, but FranxAgent is not responsible for their content).
3. Start FranxAgent – all `.md` files are automatically read and stored into the database, ready for retrieval.

**Example**:
Suppose `skills/coding_style.md` contains:
> Code style: Use 4‑space indentation, snake_case for variables, camelCase for functions.

The AI will then follow these style conventions in subsequent conversations.

> ⚠️ **Disclaimer**: Skill files are provided by users; FranxAgent assumes no responsibility for their content. Ensure the content complies with laws and does not contain sensitive or harmful information.

---

## 🔨 Tool System

FranxAgent supports loading tools from the `knowledge/tools/` directory.

**Usage**:

Copy some tools from the [tools branch](https://github.com/xhdlphzr/FranxAgent/tree/tools) (note that these tools will undergo basic reviews, but FranxAgent shall not be held responsible for their content) into the `knowledge/tools/` directory.

---

## 🧠 Memory & Scheduled Tasks

- **Long‑term memory**: FranxAgent no longer relies on `memory.txt`. Complete conversation history is automatically saved to `knowledge/memories/` (one `.md` file per session). On next startup, these histories are loaded into the vector knowledge base, allowing the AI to recall previous conversations via **hybrid retrieval (vector semantics + keyword matching)**.
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

- All friends who use and support FranxAgent
- [xhdlphzr](https://github.com/xhdlphzr) – a busy coder
- [zhiziwj](https://github.com/zhiziwj) – provided a valuable suggestion (though not implemented) and also implemented a feature
- [humanity687](https://github.com/humanity687) – raised several constructive issues, all of which have been studied and fixed