# Changelog

## [v1.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.0.0)
- Initial release of the command-line version.

## [v1.0.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.0.1)
- Tool calling capability.
- Human-friendly interactive design.

## [v1.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.1.0)
- String similarity calculation tool.
- Several fixes in tool calling.

## [v1.1.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.1.1)
- Encoding issues resolved.

## [v1.1.2](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.1.2)
- Added safety restrictions to the `command` tool, blocking direct file deletion.

## [v1.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.2.0)
- Conversation memory, enabling cross-session context retention.

## [v1.3.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.3.0)
- Execution tool.
- Improved stability of the memory feature.

## [v2.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.0.0)
- Web search tool (DuckDuckGo, free).
- Brand new web interface with real-time chat.
- One-click startup scripts (Windows `.bat` / macOS `.sh`).
- Fixed several known issues.

## [v2.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.1.0)
- Streaming output for chat responses.

## [v2.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.2.0)
- Stop generation button to interrupt AI replies at any time.
- Improved user experience details.

## [v2.3.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.3.0)
- Added more configurable parameters (temperature, max iterations, etc.).

## [v2.4.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.4.0)
- Multimodal understanding tool `ett` supporting images, videos, and document analysis.

## [v2.4.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.4.1)
- Fixed memory compatibility issues.

## [v2.5.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.5.0)
- Beijing subway route planning tool.
- Switched to GPL v3 license.

## [v3.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.0.0)
- MCP protocol support (stdio mode), connecting to any MCP server.
- Project renamed to FranxAI.
- Refactored into a "unified tool" architecture; all built-in and MCP tools are called through a single `tools` tool, significantly reducing token consumption.

## [v3.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.1.0)
- Scheduled task management in the web interface (add, delete, real-time execution).
- Scheduled task results pushed via SSE with the ability to stop mid-execution.

## [v3.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.0)
- Skill system: Markdown files in the `skills/` folder are automatically merged into the system prompt, expanding AI knowledge.
- Code refactoring and cleanup of legacy issues.

## [v3.2.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.1)
- Adjusted macOS startup scripts for better compatibility.
- Added GPL license notices to all documentation.

## [v3.2.2](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.2)
- Optimized system prompt to enhance AI behavior control.

## [v3.2.3](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.3)
- Added type restrictions to tool READMEs to ensure stable loading.

## [v3.3.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.3.0)
- Backend Markdown rendering (using `python-markdown`).
- Frontend KaTeX math formula rendering (supports `$...$` and `$$...$$`).
- User messages also support Markdown and math formulas.

## [v4.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.0.0)
- **Vector knowledge base**: Unified all knowledge sources (tool descriptions, skill files, MCP tool descriptions, conversation history) and automatically built a local vector database using `sentence-transformers` to enable semantic search.
- **Dynamic system prompt enhancement**: Before each conversation, retrieve the most relevant knowledge fragments based on user input (configurable via `knowledge_k`), dynamically inject them into the system prompt, drastically reducing token consumption while providing precise context to the AI.
- **Conversation history persistence**: Automatically save complete question‑answer pairs to the `skills/memories/` directory; on next startup they are incorporated into the vector knowledge base for cross‑session memory retrieval.
- **Unified tool entry**: Integrated built‑in and MCP tool management into the `skills` module; `agent.py` only needs to import `tool_functions` and `search`, making the code cleaner.
- **Removed `memory.txt` mechanism**: No longer rely on file‑based summaries; use vector search for long‑term memory.
- **Refactored `skills` module**: `skills/__init__.py` now handles tool loading, knowledge collection, vector database construction, and retrieval; the original `tools/` directory moved to `skills/tools/`; MCP server startup logic also migrated here.
- **New configuration `knowledge_k`**: Default value `3`, controlling how many knowledge fragments are retrieved per conversation.
- Fixed an issue where the system prompt was too verbose in multi‑turn conversations; now only the most relevant knowledge is injected.
- Fixed a missing inclusion of MCP tool descriptions in the knowledge base; the AI can now discover available tools through search.
- Removed all `memory.txt`‑related code; that file is no longer generated or read.

## [v4.0.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.0.1)
- Renamed the `skills/` directory to `knowledge/` and moved the original `skills/` into `knowledge/skills/`.

## [v4.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.1.0)
- Added deep vector search feature: supports recursive retrieval with automatic deduplication, obtaining more relevant knowledge fragments through multiple expansion steps.

## [v4.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.2.0)
- After each conversation, the question‑answer pair is immediately vectorized and stored in the knowledge base, taking effect without restart.
- On startup, only newly added, modified, or deleted `.md` files are processed, greatly improving startup speed.
- The `SentenceTransformer` model is now loaded only once and reused for subsequent searches, increasing search speed by 5‑10 times.
- Moved conversation memory backups from `skills/memories/` to `knowledge/memories/` and excluded that directory from automatic scanning; fixed a bug from v4.0.1.
- Removed `session_histories` and the batch‑write logic on exit, simplifying the code.

## [v4.3.0](https://github.com/botblock/BotBlock-Bot/releases/tag/v4.3.0)
- Full project internationalization: All comments, logs and internal prompts are fully Englishized