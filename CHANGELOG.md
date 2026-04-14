# Changelog

## [v1.0.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v1.0.0)
- Initial release of the command-line version.

## [v1.0.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v1.0.1)
- Tool calling capability.
- Human-friendly interactive design.

## [v1.1.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v1.1.0)
- String similarity calculation tool.
- Several fixes in tool calling.

## [v1.1.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v1.1.1)
- Encoding issues resolved.

## [v1.1.2](https://github.com/xhdlphzr/FranxAgent/releases/tag/v1.1.2)
- Added safety restrictions to the `command` tool, blocking direct file deletion.

## [v1.2.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v1.2.0)
- Conversation memory, enabling cross-session context retention.

## [v1.3.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v1.3.0)
- Execution tool.
- Improved stability of the memory feature.

## [v2.0.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v2.0.0)
- Web search tool (DuckDuckGo, free).
- Brand new web interface with real-time chat.
- One-click startup scripts (Windows `.bat` / macOS `.sh`).
- Fixed several known issues.

## [v2.1.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v2.1.0)
- Streaming output for chat responses.

## [v2.2.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v2.2.0)
- Stop generation button to interrupt AI replies at any time.
- Improved user experience details.

## [v2.3.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v2.3.0)
- Added more configurable parameters (temperature, max iterations, etc.).

## [v2.4.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v2.4.0)
- Multimodal understanding tool `ett` supporting images, videos, and document analysis.

## [v2.4.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v2.4.1)
- Fixed memory compatibility issues.

## [v2.5.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v2.5.0)
- Beijing subway route planning tool.
- Switched to GPL v3 license.

## [v3.0.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v3.0.0)
- MCP protocol support (stdio mode), connecting to any MCP server.
- Project renamed to FranxAgent.
- Refactored into a "unified tool" architecture; all built-in and MCP tools are called through a single `tools` tool, significantly reducing token consumption.

## [v3.1.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v3.1.0)
- Scheduled task management in the web interface (add, delete, real-time execution).
- Scheduled task results pushed via SSE with the ability to stop mid-execution.

## [v3.2.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v3.2.0)
- Skill system: Markdown files in the `skills/` folder are automatically merged into the system prompt, expanding AI knowledge.
- Code refactoring and cleanup of legacy issues.

## [v3.2.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v3.2.1)
- Adjusted macOS startup scripts for better compatibility.
- Added GPL license notices to all documentation.

## [v3.2.2](https://github.com/xhdlphzr/FranxAgent/releases/tag/v3.2.2)
- Optimized system prompt to enhance AI behavior control.

## [v3.2.3](https://github.com/xhdlphzr/FranxAgent/releases/tag/v3.2.3)
- Added type restrictions to tool READMEs to ensure stable loading.

## [v3.3.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v3.3.0)
- Backend Markdown rendering (using `python-markdown`).
- Frontend KaTeX math formula rendering (supports `$...$` and `$$...$$`).
- User messages also support Markdown and math formulas.

## [v4.0.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.0.0)
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

## [v4.0.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.0.1)
- Renamed the `skills/` directory to `knowledge/` and moved the original `skills/` into `knowledge/skills/`.

## [v4.1.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.1.0)
- Added deep vector search feature: supports recursive retrieval with automatic deduplication, obtaining more relevant knowledge fragments through multiple expansion steps.

## [v4.2.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.2.0)
- After each conversation, the question‑answer pair is immediately vectorized and stored in the knowledge base, taking effect without restart.
- On startup, only newly added, modified, or deleted `.md` files are processed, greatly improving startup speed.
- The `SentenceTransformer` model is now loaded only once and reused for subsequent searches, increasing search speed by 5‑10 times.
- Moved conversation memory backups from `skills/memories/` to `knowledge/memories/` and excluded that directory from automatic scanning; fixed a bug from v4.0.1.
- Removed `session_histories` and the batch‑write logic on exit, simplifying the code.

## [v4.3.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.3.0)
- Full project internationalization: All comments, logs and internal prompts are fully Englishized.

## [v4.4.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.4.0)
- Added type‑based weighting to vector search: tool documents (type='tool') now get full weight 1.0, skills (type='skill') 0.8, and conversation memories (type='conversation') 0.2. This improves retrieval relevance by prioritizing actionable tools over background knowledge and suppressing noisy dialogue history.

## [v4.4.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.4.1)
- Reduce redundant memory, fix i18n legacy bugs.

## [v4.5.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.5.0)
- Added hybrid search (vector + FTS5) combining semantic similarity with keyword matching for more accurate knowledge retrieval.
- Added type‑based weighting: tools (1.0) have higher priority than skills (0.8) and conversation memories (0.2).
- Added Reciprocal Rank Fusion (RRF) to merge vector and FTS rankings into a single score.
- Automatic document type detection (tool, skill, conversation) during incremental updates.
- Removed length penalty – long documents are no longer suppressed, improving retrieval quality.
- Replaced recursive deep search with breadth‑first single‑shot hybrid retrieval, improving speed and predictability.
- Adjusted document language order: English descriptions moved before Chinese to fit vector model’s token limit; Chinese keywords are still fully indexed by FTS.
- Added FTS query cleaning to remove special characters (e.g., `<`, `>`, `:`) and prevent syntax errors.
- `knowledge/memories/` directory is now included in incremental update scanning; deleting backup files will remove corresponding vector entries.
- Fixed identical vectors for all tools by removing the copyright comment block from each README, ensuring only meaningful content is vectorised.
- Fixed skill documents dominating search results by adjusting type weights, document language order, and relying on FTS for keyword matching.
- Fixed incremental update ignoring the `memories/` directory by including it in file state collection.

## [v4.6.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.6.0)
- New animation system **Breath of Motion**: Introduces liquid glass bottom dock, page sliding transitions, AI reply breathing dot, and smooth expand/collapse animations for the console and knowledge panel.
- Added RSA password authentication: Automatically generates a key pair on first run, encrypts password with public key on the frontend, decrypts with private key on the backend, enhancing login security.
- Added JWT session management: Issues short-lived tokens (default 1 hour) after login, supports "refresh-to-re-login" mode (token stored only in memory, cleared on page refresh).
- Integrated Cloudflare Tunnel: One‑click temporary tunnel to generate a publicly accessible URL, enabling remote access without a public IP.
- Full mobile adaptation: Replaces sidebar with bottom dock, optimizes message bubbles and input area for touchscreens, supports phones and tablets.
- Knowledge panel refactoring: Collapsible panel that displays retrieved knowledge, each item can be independently expanded to view full text, uses tech‑blue color scheme, scroll support for long documents.
- Console no longer auto‑opens: User must click to open, avoiding interruption of the chat experience.
- Added empty‑text check when inserting conversation memory into the vector database in real time, preventing invalid records from polluting search results.

## [v4.6.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.6.1)
- Fixed the issue in `agent.py` where multi‑turn conversation history was being reset; consecutive `input` calls on the same `FranxAgent` instance now correctly retain context.  
- Optimized system prompt delivery: `USER_GUIDE` is sent only once at the beginning of the session, no longer repeated in every turn, significantly reducing token usage.  
- Dynamically retrieved knowledge is now injected as a temporary system message without polluting the persistent conversation history.  
- Fixed message synchronization in the tool‑calling loop, ensuring tool results are correctly appended to the history.  
- Additional minor improvements and code comment updates.

## [v4.6.2](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.6.2)
- Change `USER_GUIDE` in `agent.py`.

## [v4.6.3](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.6.3)
- Fixed hardcoded Flask `app.secret_key` security issue; now reads randomly generated key from `config.json` (auto‑generated on first start). Previously hardcoded for convenience, sorry.

## [v4.7.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.7.0)
- Removed the `base_url` field for the `ett` tool from `config.json` as it is no longer needed.  
- Improved user experience: automatically copy `config.example.json` and rename it to `config.json` on startup, so users don’t need to do it manually.  
- Added a click‑to‑confirm disclaimer checkbox that users must check before continuing to use.
- Added shake animation.

## [v4.7.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.7.1)
- Added `.gitignore` file.

## [v4.8.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.8.0)
- Added full-platform shared conversation history feature.
- Fixed partial response save issue.

## [v4.8.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.8.1)
- Changed `README.md`.

## [v4.8.2](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.8.2)
- Changed `USER_GUIDE` in `src/agent.py`.

## [v4.8.3](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.8.3)
- Fixed `src/templates/index.html` math formula rendering issue.
- Fixed animation priority bug.

## [v4.9.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.9.0)
- Changed the order of tools and messages to be sorted by time.
- Added confirmation feature for the `command` and `write` tools.
- Fixed some known issues.
- Renamed to `FranxAgent`.

## [v4.9.1](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.9.1)
- Fixed documentation.

## [v4.10.0](https://github.com/xhdlphzr/FranxAgent/releases/tag/v4.10.0)
- `read` tool merged the functionality of `ett` tool, and the file part is now handled by `markitdown` tool.
- Fixed documentation.