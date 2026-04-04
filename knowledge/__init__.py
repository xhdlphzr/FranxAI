# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module: Unified tool loading + MCP management + Automatic vector knowledge base construction (supports incremental updates) | Knowledge 模块：统一工具加载 + MCP 管理 + 自动构建向量知识库（支持增量更新）
"""

import importlib.util
import sys
import sqlite3
import json
import numpy as np
import time
import threading
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Add project root directory to sys.path for importing src.mcps | 添加项目根目录到 sys.path 以便导入 src.mcps
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcps import MCPStdioClient

# Global Model (Singleton) | 全局模型（单例）
_model = None
MODEL_NAME = 'all-MiniLM-L12-v2'

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

# 1. Load Built-in Tools | 加载内置工具
KNOWLEDGE_ROOT = Path(__file__).parent
TOOLS_DIR = KNOWLEDGE_ROOT / 'tools'
MEMORIES_DIR = KNOWLEDGE_ROOT / 'memories'   # Conversation memory backup directory (not included in automatic scanning) | 对话记忆备份目录（不参与自动扫描）

# Create memories directory if it does not exist | 创建 memories 目录（如果不存在）
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

_internal_tools = {}
for item in TOOLS_DIR.iterdir():
    if not item.is_dir() or item.name.startswith('__'):
        continue
    tool_name = item.name
    tool_path = item / 'tool.py'
    readme_path = item / 'README.md'

    if not (tool_path.exists() and readme_path.exists()):
        print(f"⚠️ Tool {tool_name} is missing tool.py or README.md, skipping | 工具 {tool_name} 缺少 tool.py 或 README.md，跳过")
        continue

    try:
        spec = importlib.util.spec_from_file_location(f"knowledge.tools.{tool_name}", tool_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"knowledge.tools.{tool_name}"] = module
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"⚠️ Failed to import tool.py for {tool_name}: {e}, skipping | 工具 {tool_name} 的 tool.py 导入失败：{e}，跳过")
        continue

    if not hasattr(module, 'execute'):
        print(f"⚠️ tool.py for {tool_name} does not define execute function, skipping | 工具 {tool_name} 的 tool.py 未定义 execute 函数，跳过")
        continue

    _internal_tools[tool_name] = module.execute

# 2. Collect All Markdown Files (Exclude memories directory) | 收集所有 Markdown 文件（排除 memories 目录）
def _get_file_state():
    """Get the status of all current .md files (path -> mtime) | 获取当前所有 .md 文件的状态（路径 -> 修改时间）"""
    state = {}
    # 递归遍历 KNOWLEDGE_ROOT 下所有 .md 文件，排除 memories 目录
    for md_file in KNOWLEDGE_ROOT.rglob("*.md"):
        # Skip the memories directory and its subdirectories | 跳过 memories 目录及其子目录
        if MEMORIES_DIR in md_file.parents or md_file.parent == MEMORIES_DIR:
            continue
        try:
            mtime = md_file.stat().st_mtime
            state[str(md_file.relative_to(KNOWLEDGE_ROOT))] = mtime
        except Exception as e:
            print(f"⚠️ Failed to get file status {md_file}: {e} | 无法获取文件状态 {md_file}: {e}")
    return state

# 3. MCP Server Management | MCP 服务器管理
_mcp_tools = {}
_mcp_clients = []
_mcp_lock = threading.Lock()

def _load_mcp_servers():
    """Load and start MCP servers from config file, add tool descriptions to knowledge base (dynamic addition) | 从配置文件加载 MCP 服务器并启动，将工具描述加入知识库（动态添加）"""
    global _mcp_tools
    config_path = PROJECT_ROOT / "config.json"
    if not config_path.exists():
        return
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Failed to read config file: {e} | 读取配置文件失败: {e}")
        return

    servers = config.get("mcp_servers", [])
    if not servers:
        return

    for server in servers:
        name = server.get("name", "unknown")
        command = server.get("command")
        if not command:
            print(f"Skipping {name}: missing command | 跳过 {name}: 缺少 command")
            continue
        args = server.get("args", [])

        try:
            client = MCPStdioClient(command, args)
            client.start()
            time.sleep(0.5)  # Wait for subprocess to be ready | 等待子进程就绪
            raw_tools = client.list_tools()
            if not raw_tools:
                print(f"⚠️ {name} returned no tools, skipping | {name} 未返回工具，跳过")
                client.close()
                continue

            print(f"Connected to MCP server {name}, found {len(raw_tools)} tools | 已连接 MCP 服务器 {name}，发现 {len(raw_tools)} 个工具")
            _mcp_clients.append(client)
            with _mcp_lock:
                for tool in raw_tools:
                    tool_name = tool["name"]
                    full_name = f"{name}/{tool_name}"
                    description = tool.get("description", "")
                    params = tool.get("inputSchema", {}).get("properties", {})
                    param_str = ", ".join([f"{k} ({v.get('type','any')})" for k, v in params.items()])
                    desc_text = f"Tool name: {full_name}\nFunction: {description}\nParameters: {param_str}" if param_str else f"Tool name: {full_name}\nFunction: {description}"
                    # To avoid duplicates, check if the description exists in the database; insert directly for simplicity (may duplicate, deduplication handled by search rtn) | 为避免重复，可以检查数据库中是否已有该描述，简单起见直接插入（可能重复，但去重由 search 的 rtn 处理）
                    _add_document(desc_text, source=f"mcp_{full_name}", doc_type="mcp")

                    # Create wrapper function | 创建包装函数
                    def make_wrapper(mcp_client, t_name):
                        def wrapper(**kwargs):
                            try:
                                return mcp_client.call_tool(t_name, kwargs)
                            except Exception as e:
                                return f"Call failed: {e} | 调用失败: {e}"
                        return wrapper
                    _mcp_tools[full_name] = make_wrapper(client, tool_name)
        except Exception as e:
            print(f"Failed to start MCP server {name}: {e} | 启动 MCP 服务器 {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            continue

# Helper function: Insert a single document into the vector library | 辅助函数：向向量库插入单个文档
def _add_document(text: str, source: str = "", doc_type: str = "generic"):
    """Insert document directly (no rebuild) | 直接插入文档（不重建）"""
    model = _get_model()
    emb = model.encode(text)
    emb_blob = emb.tobytes()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Check if the same text already exists (optional, avoid duplicates) | 检查是否已存在相同文本（可选，避免重复）
    cursor.execute("SELECT id FROM vectors WHERE text = ?", (text,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO vectors (text, embedding, source, type) VALUES (?, ?, ?, ?)",
            (text, emb_blob, source, doc_type)
        )
        conn.commit()
    conn.close()

# Start MCP servers (they will call _add_document to dynamically add descriptions) | 启动 MCP 服务器（它们会调用 _add_document 动态添加描述）
_load_mcp_servers()

# 4. Vector Library Incremental Update | 向量库增量更新
VECTOR_DB_PATH = KNOWLEDGE_ROOT / "knowledge.db"

def _init_vector_db():
    """Create database tables if they do not exist, and add missing columns | 创建数据库表（如果不存在），并添加缺失的列"""
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_versions (
            path TEXT PRIMARY KEY,
            mtime REAL,
            last_updated REAL
        )
    ''')
    # Add missing columns if they do not exist | 添加缺失的列（如果不存在）
    try:
        cursor.execute("ALTER TABLE vectors ADD COLUMN source TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists | 列已存在
    try:
        cursor.execute("ALTER TABLE vectors ADD COLUMN type TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def _incremental_update():
    """Incremental update: Compare current file status with file_versions table, re-vectorize and update new/modified files, delete corresponding records from vectors table for deleted files. | 增量更新：对比当前文件状态与 file_versions 表，对新增/修改的文件重新向量化并更新，对删除的文件从 vectors 表中删除对应的记录。"""
    print("Performing incremental vector library update... | 正在执行增量向量库更新...")
    current_state = _get_file_state()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Get stored file status | 获取已存储的文件状态
    cursor.execute("SELECT path, mtime FROM file_versions")
    stored = {row[0]: row[1] for row in cursor.fetchall()}

    # 1. Process new or modified files | 处理新增或修改的文件
    for path, mtime in current_state.items():
        if path not in stored or stored[path] != mtime:
            # Needs update | 需要更新
            file_path = KNOWLEDGE_ROOT / path
            try:
                text = file_path.read_text(encoding='utf-8').strip()
                if not text:
                    continue
                # Delete old records if they exist | 删除旧记录（如果存在）
                cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
                # Insert new vector | 插入新向量
                model = _get_model()
                emb = model.encode(text)
                emb_blob = emb.tobytes()
                cursor.execute(
                    "INSERT INTO vectors (text, embedding, source, type) VALUES (?, ?, ?, ?)",
                    (text, emb_blob, f"file:{path}", "skill")
                )
                # Update file_versions table | 更新 file_versions 表
                cursor.execute(
                    "INSERT OR REPLACE INTO file_versions (path, mtime, last_updated) VALUES (?, ?, ?)",
                    (path, mtime, time.time())
                )
                print(f"Updated: {path} | 已更新: {path}")
            except Exception as e:
                print(f"⚠️ Failed to update file {path}: {e} | 更新文件 {path} 失败: {e}")

    # 2. Process deleted files (not in current_state but exist in stored) | 处理删除的文件（在 current_state 中不存在，但在 stored 中存在）
    for path in stored:
        if path not in current_state:
            cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
            cursor.execute("DELETE FROM file_versions WHERE path = ?", (path,))
            print(f"Deleted: {path} | 已删除: {path}")

    conn.commit()
    conn.close()
    print("Incremental update completed. | 增量更新完成。")

def _full_rebuild():
    """Full rebuild (for first run or complete reset) | 全量重建（用于初次运行或需要完全重置）"""
    print("Performing full vector library rebuild... | 执行全量向量库重建...")
    # Clear all tables | 清空所有表
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vectors')
    cursor.execute('DELETE FROM file_versions')
    conn.commit()
    conn.close()
    # Reinsert all files | 重新插入所有文件
    _incremental_update()

# Initialize database | 初始化数据库
_init_vector_db()

# Check if first build is needed: If vectors table is empty, full rebuild; else incremental update | 检查是否需要首次构建：若 vectors 表为空，则全量重建；否则增量更新
conn = sqlite3.connect(VECTOR_DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM vectors")
count = cursor.fetchone()[0]
conn.close()
if count == 0:
    _full_rebuild()
else:
    _incremental_update()

# 5. Retrieval Interface (Supports Recursive Expansion + Deduplication) | 检索接口（支持递归扩展 + 去重）
def search(query: str, k: int = 1, step: int = 1, rtn: list = None):
    """
    Retrieve the top k knowledge entries most similar to the query (automatic deduplication, recursive expansion) | 检索与 query 最相似的 k 条知识（自动去重，递归扩展）
    Return a list of strings (each knowledge entry is plain text) | 返回字符串列表（每条知识为纯文本）
    """
    if rtn is None:
        rtn = []

    if step > k:
        return rtn

    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Also read the type field | 同时读取 type 字段
    cursor.execute("SELECT text, embedding, type FROM vectors")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return []

    model = _get_model()
    q_emb = model.encode(query)
    scores = []
    for text, emb_blob, doc_type in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        dot = np.dot(q_emb, emb)
        norm_q = np.linalg.norm(q_emb)
        norm_d = np.linalg.norm(emb)
        sim = dot / (norm_q * norm_d) if norm_q * norm_d != 0 else 0

        # Apply type weights: tool=1.0, skill=0.8, conversation=0.2, default=1.0 | 应用类型权重：工具=1.0，技能=0.8，对话=0.2，默认=1.0
        if doc_type == 'tool':
            weight = 1.0
        elif doc_type == 'skill':
            weight = 0.8
        elif doc_type == 'conversation':
            weight = 0.2
        else:
            weight = 1.0  # Default for mcp or unknown types | MCP 或未知类型默认 1.0

        final_score = sim * weight
        scores.append((final_score, text))
    scores.sort(reverse=True, key=lambda x: x[0])

    # Deduplicate: select the first result not in rtn | 去重选择第一个未在 rtn 中的结果
    selected = None
    for score, text in scores:
        if text not in rtn:
            selected = (score, text)
            break
    if selected is None:
        return rtn

    rtn.append(selected[1])
    # Build new query (accumulate selected results) | 构建新查询（累积已选结果）
    ans = "\n\n".join(rtn)
    return search(query + ans, k, step + 1, rtn)

# 6. Dynamically Insert Conversation Memory | 动态插入对话记忆
def add_conversation(user_msg: str, ai_msg: str):
    """
    Dynamically insert a round of Q&A into the vector library (takes effect in real time), and back up to the knowledge/memories/ directory | 将一轮问答动态插入向量库（实时生效），同时备份到 knowledge/memories/ 目录
    """
    text = f"User: {user_msg}\nAI: {ai_msg} | 用户：{user_msg}\nAI：{ai_msg}"
    # Insert into vector library | 插入向量库
    _add_document(text, source=f"conv_{int(time.time())}", doc_type="conversation")

    backup_file = MEMORIES_DIR / f"{int(time.time())}_{hash(text) & 0xFFFFFFFF}.md"
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"⚠️ Failed to write memory backup: {e} | 写入记忆备份失败: {e}")

# 7. Unified Tool Call (Built-in + MCP) | 统一工具调用（内置 + MCP）
def tools(tool_name: str, arguments: dict = None) -> str:
    """
    Unified tool call interface: Supports built-in tools and MCP tools (format: server_name/tool_name) | 统一工具调用接口：支持内置工具和 MCP 工具（格式 服务器名/工具名）
    """
    # First check if it is an MCP tool | 先检查是否是 MCP 工具
    if '/' in tool_name:
        with _mcp_lock:
            if tool_name in _mcp_tools:
                try:
                    return _mcp_tools[tool_name](**(arguments or {}))
                except Exception as e:
                    return f"MCP tool call failed: {e} | MCP 工具调用失败: {e}"
            else:
                return f"Error: Unknown MCP tool {tool_name} | 错误：未知 MCP 工具 {tool_name}"
    # Otherwise try built-in tools | 否则尝试内置工具
    if tool_name not in _internal_tools:
        return f"Error: Unknown tool {tool_name} | 错误：未知工具 {tool_name}"
    try:
        return _internal_tools[tool_name](**(arguments or {}))
    except Exception as e:
        return f"Call failed: {e} | 调用失败: {e}"

# Export tool function dictionary (only one tools function) | 导出工具函数字典（只有一个 tools 函数）
tool_functions = {"tools": tools}

# Tool metadata (description) | 工具元数据（描述）
tools_metadata = [
    {
        "type": "function",
        "function": {
            "name": "tools",
            "description": "Call any available tool. Parameters: tool_name (tool name), arguments (JSON object). All built-in tools are called through this tool. | 调用任何可用工具。参数：tool_name (工具名), arguments (JSON 对象)。所有内置工具都通过此工具调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Tool name, e.g., read, write, command, search, similarity, add_task, del_task, ett, beijing_subway, etc. External MCP tools use the format server_name/tool_name. | 工具名称，如 read、write、command、search、similarity、add_task、del_task、ett、beijing_subway 等。外部 MCP 工具使用 服务器名/工具名 格式。"
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Tool parameters | 工具参数"
                    }
                },
                "required": ["tool_name"]
            }
        }
    }
]

# Cleanup function (for external calls, e.g., atexit) | 清理函数（供外部调用，例如 atexit）
def cleanup_mcp_clients():
    """Close all MCP clients | 关闭所有 MCP 客户端"""
    for client in _mcp_clients:
        try:
            client.close()
        except:
            pass

print("Built-in tool list | | 内置工具列表：", list(_internal_tools.keys()))
print(f"MCP tool count | MCP 工具数量：{len(_mcp_tools)}")
print("Knowledge base incremental update completed. | 知识库增量更新已完成。")

__all__ = ['tools_metadata', 'tool_functions', 'search', 'cleanup_mcp_clients', 'add_conversation']