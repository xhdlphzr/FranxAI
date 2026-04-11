# Changelog

## [v1.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.0.0)
- 命令行版本初始发布。

## [v1.0.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.0.1)
- 工具调用能力。
- 人性化交互设计。

## [v1.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.1.0)
- 字符串相似度计算工具。
- 工具调用中的若干问题。

## [v1.1.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.1.1)
- 编码问题。

## [v1.1.2](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.1.2)
- `command` 工具增加安全限制，禁止直接删除文件。

## [v1.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.2.0)
- 对话记忆功能，支持跨会话保留上下文。

## [v1.3.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v1.3.0)
- 执行工具。
- 记忆功能的稳定性。

## [v2.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.0.0)
- 网络搜索工具（DuckDuckGo，免费）。
- 全新 Web 界面，支持实时聊天。
- 一键启动脚本（Windows `.bat` / macOS `.sh`）。
- 若干已知问题。

## [v2.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.1.0)
- 聊天响应改为流式输出。

## [v2.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.2.0)
- 停止生成按钮，可随时中断 AI 回复。
- 优化用户体验细节。

## [v2.3.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.3.0)
- 增加更多可配置参数（温度、最大迭代次数等）。

## [v2.4.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.4.0)
- 多模态理解工具 `ett`，支持图片、视频、文档分析。

## [v2.4.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.4.1)
- 记忆功能兼容性问题。

## [v2.5.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v2.5.0)
- 北京地铁换乘规划工具。
- 切换至 GPL v3 许可证。

## [v3.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.0.0)
- MCP 协议支持（stdio 模式），可连接任意 MCP 服务器。
- 项目更名为 FranxAI。
- 重构为“大一统工具”架构，所有内置工具及 MCP 工具统一通过 `tools` 调用，显著降低 token 消耗。

## [v3.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.1.0)
- Web 界面中添加定时任务管理（添加、删除、实时执行）。
- 定时任务执行结果通过 SSE 实时推送，支持中途停止。

## [v3.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.0)
- 技能系统：`skills/` 文件夹下的 Markdown 文件自动合并到系统提示，扩展 AI 知识。
- 代码重构，清理历史遗留问题。

## [v3.2.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.1)
- macOS 启动脚本兼容性调整。
- 为所有文档添加 GPL 许可声明。

## [v3.2.2](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.2)
- 系统提示词优化，增强 AI 行为可控性。

## [v3.2.3](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.2.3)
- 为工具 README 添加类型限制，确保加载稳定。

## [v3.3.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v3.3.0)
- 后端 Markdown 渲染（`python-markdown`）。
- 前端 KaTeX 数学公式渲染（支持 `$...$` 和 `$$...$$`）。
- 用户消息同样支持 Markdown 和数学公式。

## [v4.0.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.0.0)
- **向量知识库**：统一所有知识源（工具说明、技能文件、MCP 工具描述、对话历史），通过 `sentence-transformers` 自动构建本地向量库，实现语义检索。
- **动态系统提示增强**：每次对话前，根据用户输入从向量库检索最相关的知识片段（数量可配置 `knowledge_k`），动态注入系统提示，大幅降低 token 消耗，同时让 AI 获得精准上下文。
- **对话历史持久化**：将完整对话问答对自动保存到 `skills/memories/` 目录，下次启动时自动纳入知识库，实现跨会话“记忆”检索。
- **统一工具入口**：将内置工具、MCP 工具的管理全部整合到 `skills` 模块，`agent.py` 仅需导入 `tool_functions` 和 `search`，代码更简洁。
- **移除 `memory.txt` 机制**：不再依赖文件摘要，改用向量库检索实现长期记忆。
- **`skills` 模块重构**：`skills/__init__.py` 现在同时负责工具加载、知识收集、向量库构建与检索；原 `tools/` 目录移入 `skills/tools/`，MCP 服务器启动逻辑也迁移至此。
- **配置新增 `knowledge_k`**：默认值 `3`，控制每次检索的知识片段数量。
- 修复了多轮对话中系统提示过于冗长的问题，现在只注入最相关的知识。
- 解决了 MCP 工具描述未加入知识库的遗漏，AI 现在能通过检索发现可用工具。
- 删除 `memory.txt` 相关代码，不再生成或读取该文件。

## [v4.0.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.0.1)
- 将 `skills/` 目录改名为 `knowledge/` 目录，并将原本的 `skills/` 迁移到 `knowledge/skills/`。

## [v4.1.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.1.0)
- 增加深度向量库功能：支持递归检索 + 自动去重，通过多次扩展查询获取更相关的知识片段。

## [v4.2.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.2.0)
- 对话结束后立即将问答对向量化并存入知识库，无需重启即可生效。
- 启动时仅处理新增、修改或删除的 `.md` 文件，大幅提升启动速度。
- `SentenceTransformer` 模型只加载一次，后续检索复用，搜索速度提升 5~10 倍。
- 对话记忆备份从 `skills/memories/` 移至 `knowledge/memories/`，并排除该目录的自动扫描，更改了v4.0.1的bug。
- 删除 `session_histories` 及退出时批量写入逻辑，简化代码。

## [v4.3.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.3.0)
- 项目全面国际化：所有注释、日志、内部提示完全英文化。

## [v4.4.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.4.0)
- 为向量检索增加了基于类型的权重：工具文档（type='tool'）权重为 1.0，技能（type='skill'）为 0.8，对话记忆（type='conversation'）为 0.2。这一改进优先返回可操作的工具，降低背景知识和对话历史噪音，提升检索相关性。

## [v4.4.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.4.1)
- 减少冗余记忆，解决i18n遗留bug。

## [v4.5.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.5.0)
- 新增混合搜索（向量 + FTS5），结合语义相似度与关键词匹配，提升知识检索准确性。  
- 新增基于类型的权重：工具（1.0）优先级高于技能（0.8）和对话记忆（0.2）。
- 新增倒数排名融合（RRF），将向量和 FTS 的排名合并为单一得分。
- 增量更新时自动检测文档类型（工具、技能、对话），正确标记类型。
- 移除长度惩罚，不再压制长文档，检索质量提升。
- 将递归深度搜索改为广度优先（单次混合检索），提高检索速度和结果可预测性。
- 调整文档语言顺序：英文描述移至中文之前，以适应向量模型的 token 限制；中文关键词仍被 FTS 完整索引 
- 增加 FTS 查询清洗，移除特殊字符（如 `<`、`>`、`:`），防止语法错误。
- `knowledge/memories/` 目录现在被纳入增量更新扫描，删除备份文件可同步清除向量记录。
- 修复所有工具向量相同的问题：删除每个 README 开头的版权注释块，确保只有有意义的内容被向量化
- 修复技能文档霸占搜索结果的问题：通过调整类型权重、文档语言顺序以及依赖 FTS 进行关键词匹配解决。
- 修复增量更新忽略 `memories/` 目录的问题：将该目录纳入文件状态收集。

## [v4.6.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.6.0)
- 全新动画系统 **Breath of Motion**：引入液态玻璃底部 Dock、页面滑动切换、AI 回复呼吸小球，以及控制台和知识面板的平滑伸缩动画。
- 增加 RSA 密码认证：首次启动自动生成密钥对，前端公钥加密传输，后端私钥解密，提升登录安全性。
- 增加 JWT 会话管理：登录后签发短期令牌（默认 1 小时），支持“刷新即重登”模式（令牌仅存内存，刷新页面即失效）。
- 集成 Cloudflare Tunnel：一键启动临时隧道，生成公网可访问 URL，无需公网 IP 即可远程访问。
- 移动端全面适配：底部 Dock 替代侧边栏，消息气泡、输入框触屏优化，支持手机、平板等小屏幕设备。
- 知识面板重构：可折叠面板统一展示检索到的相关知识，每个条目可独立展开查看全文，采用科技蓝配色，长文档支持滚动。
- 控制台不再自动展开：由用户主动点击打开，避免干扰聊天体验。
- 增加对话记忆实时插入向量库时的空文本检查，避免无效记录污染检索结果。

## [v4.6.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.6.1)
- 修复 `agent.py` 中多轮对话历史被重置的问题，现在同一 `FranxAI` 实例的多次 `input` 调用能够正确保留上下文。  
- 优化系统提示发送策略：`USER_GUIDE` 仅在会话开始时发送一次，不再每轮重复，显著降低 token 消耗。  
- 动态检索的知识现在以临时系统消息注入，不影响持久化对话历史。  
- 修复工具调用循环中消息同步问题，确保工具结果正确追加到历史中。  
- 其他细节改进与代码注释优化。

## [v4.6.2](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.6.2)
- 更改 `agent.py` 中的 `USER_GUIDE`。

## [v4.6.3](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.6.3)
- 修复 Flask 的 `app.secret_key` 硬编码安全漏洞，改为从 `config.json` 读取随机生成的密钥（首次启动自动生成）。以前为了图省事直接在代码中写死，对不起。

## [v4.7.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.7.0)
- 删除了 `config.json` 中 `ett` 工具的 `base_url` 字段，因为不再需要。
- 调整用户体验，启动时自动复制 `config.example.json` 并改名为 `config.json`，用户无需手动操作。
- 增加点击确认免责声明框，用户必须点击确认后才能继续使用。
- 新增了抖动动画。

## [v4.7.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.7.1)
- 增加 `.gitignore` 文件。

## [v4.8.0](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.8.0)
- 增加了全平台共享聊天记录的功能。
- 修复了部分回复内容保存问题。

## [v4.8.1](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.8.1)
- 更改了 `README.md`

## [v4.8.2](https://github.com/xhdlphzr/FranxAI/releases/tag/v4.8.2)
- 更改了 `src/agent.py` 内的 `USER_GUIDE`