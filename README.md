# FranxAgent 🤖

**English** | [中文](docs/zh/README.md)

**Let AI work for you like a partner – simple, secure, low cost.**  
**Now you can control the AI on your computer directly from your phone – no public IP, no port forwarding, one‑click secure remote access.**

FranxAgent is a lightweight AI agent framework that enables AI to read files, execute commands, search the web, understand multimodal content, and truly interact with the world through the MCP protocol.  
**v5.0.0 introduces a revolutionary Code Review Panel that transforms how you collaborate with AI on code changes – no more blind approvals, every edit is visible and editable before it touches your files.**

---

## 🎉 What's New in v5.0.0

- 🔍 **Code Review Panel**: When the AI proposes file changes, a full‑featured code editor slides in from the right, showing syntax‑highlighted code with **red (deletion) and green (addition) diff markers**. You can switch between **view mode** and **edit mode**, modify the code directly, and only apply changes when you approve. No more "blind trust" – every line is reviewed before it reaches your disk.
- 📊 **Mermaid diagram rendering**: Chat messages now render Mermaid diagrams as live SVGs – flowcharts, sequence diagrams, and more, directly in the conversation.
- 📜 **Smart scrolling**: The chat intelligently auto‑scrolls only when you're at the bottom; scroll up to review history without interruption.
- ✍️ **Write tool reborn**: The `write` tool no longer modifies files directly. It sends AI proposals to the frontend, where you review, edit, and approve changes – putting you firmly in control.

---

## ✨ Core Features

- 📱 **Zero‑configuration remote access**: integrated Cloudflare Tunnel – one‑click public URL, no public IP or router settings needed. Access FranxAgent on your computer directly from your phone/tablet.
- 🔐 **Military‑grade security authentication**: RSA asymmetric encryption + JWT short‑lived tokens, supports "refresh‑to‑re‑login" (token stored only in memory, cleared on page refresh), completely prevents long‑term control after token leakage.
- 🧠 **Intelligent memory & hybrid search**: conversation history automatically stored in vector database, combined with FTS5 keyword search for precise cross‑session recall.
- 🛠️ **Rich built‑in tools**: `read`, `write`, `command`, `search`, `add_skill`, etc., extensible.
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

## 🔍 The Code Review Panel (v5.0.0)

The Code Review Panel is the centrepiece of v5.0.0. When the AI uses the `write` tool, instead of modifying your file immediately, a full‑featured code editor slides in from the right side of the chat:

- **Syntax highlighting**: Powered by CodeMirror 5, with automatic language detection based on file extension (Python, JavaScript, C/C++, Rust, Go, and more).
- **Diff markers**: Deleted lines appear with red semi‑transparent background; added lines appear with green semi‑transparent background. Line numbers are colour‑coded to match.
- **View mode**: Read‑only, with full diff visibility. Inspect every change the AI proposes.
- **Edit mode**: One click to switch – the editor becomes fully editable. Modify the AI's proposal, fix mistakes, or add your own touches.
- **Approve or reject**: Only when you click "Approve" does the final code reach your file. Reject to discard the proposal entirely.
- **Smooth animations**: The panel slides in from the right and slides out when dismissed.

This transforms FranxAgent from an "AI that writes code" into an "AI that collaborates on code with you."

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
Type your question in the chat box – the AI will automatically call tools to help you. The mobile experience is identical to the desktop version, with touch, swipe, and voice input support (via the phone's own input methods).

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
| `settings` | string | `"You are a helpful AI assistant."` | System prompt defining AI's role or behaviour. |
| `temperature` | float | `0.8` | Randomness, range 0–2 (but recommended 0–1). Lower = more deterministic, higher = more creative. |
| `thinking` | bool | `false` | Enable deep thinking mode (GLM models only). The model outputs reasoning steps but responds slightly slower. |
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
    "knowledge_k": 5,
    "settings": "You are a helpful AI assistant.",
    "tools": {
        "ett": {
            "api_key": "your-zhipu-api-key",
            "model": "glm-4.6v-flash",
            "temperature": 0.8,
            "thinking": false,
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
| `read` | Read file content or project structure | Read‑only. Code files return AST structure + line‑numbered content; directories return project skeleton. Supports documents, images, videos. |
| `write` | Propose file changes (review‑before‑write) | **v5.0.0**: No longer writes files directly. Sends AI proposals to the Code Review Panel, where you review diffs, edit code, and approve changes. Supports `overwrite`, `append`, and `edit` modes. |
| `command` | Execute system command | ❌ Direct deletion blocked; suggests moving instead. Supports timeout. |
| `search` | Web search (DuckDuckGo) | Free, no API key. Returns title, snippet, URL. |
| `add_skill` | Save a reusable skill | Saves Markdown skill file and immediately indexes it into the vector database. Zero restart, real‑time retrieval. No confirmation needed. |

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
After startup, the AI automatically discovers all tools from these servers and calls them via the unified `tools` tool. No extra configuration – just say "take a screenshot".

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
- **Scheduled tasks**: Background thread checks `tasks.json` every 10 seconds; executes commands at specified times (HH:MM). Supports daily repetition without duplication.

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