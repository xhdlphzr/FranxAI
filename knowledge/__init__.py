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
import re
from pathlib import Path
from datetime import datetime
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

# Hybrid search is always enabled (weights: vector 0.7, fts 0.3) | 混合搜索始终启用
_HYBRID_VECTOR_WEIGHT = 0.7
_HYBRID_FTS_WEIGHT = 0.3

# 1. Load Built-in Tools | 加载内置工具
KNOWLEDGE_ROOT = Path(__file__).parent
TOOLS_DIR = KNOWLEDGE_ROOT / 'tools'
MEMORIES_DIR = KNOWLEDGE_ROOT / 'memories'   # Conversation memory backup directory | 对话记忆备份目录

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

# 2. Collect All Markdown Files (including memories directory) | 收集所有 Markdown 文件（包括 memories 目录）
def _get_file_state():
    """Get the status of all current .md files (path -> mtime) | 获取当前所有 .md 文件的状态（路径 -> 修改时间）"""
    state = {}
    # 递归遍历 KNOWLEDGE_ROOT 下所有 .md 文件，包括 memories 目录
    for md_file in KNOWLEDGE_ROOT.rglob("*.md"):
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

# Helper function: Insert a single document into the vector library and FTS index | 辅助函数：向向量库插入单个文档并更新 FTS 索引
def _add_document(text: str, source: str = "", doc_type: str = "generic"):
    """Insert document directly (no rebuild) | 直接插入文档（不重建）"""
    model = _get_model()
    emb = model.encode(text)
    emb_blob = emb.tobytes()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Check if the same text already exists (optional, avoid duplicates) | 检查是否已存在相同文本（可选，避免重复）
    cursor.execute("SELECT id FROM vectors WHERE text = ?", (text,))
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO vectors (text, embedding, source, type) VALUES (?, ?, ?, ?)",
            (text, emb_blob, source, doc_type)
        )
        # Get the newly inserted rowid | 获取新插入的行 id
        new_id = cursor.lastrowid
        # Also insert into FTS table | 同时插入 FTS 表
        try:
            cursor.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (new_id, text))
        except sqlite3.OperationalError as e:
            # FTS table may not exist yet (first run), ignore | FTS 表可能尚未创建（首次运行），忽略
            if "no such table" not in str(e):
                raise
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
    # Create FTS5 virtual table for hybrid search | 创建 FTS5 虚拟表用于混合搜索
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
            text,
            tokenize = 'unicode61'
        )
    ''')
    conn.commit()
    conn.close()

def _rebuild_fts_index():
    """Rebuild the FTS index from the vectors table | 从 vectors 表重建 FTS 索引"""
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Delete all existing FTS entries | 删除所有现有 FTS 条目
    cursor.execute("DELETE FROM fts")
    # Insert all texts from vectors table | 插入所有文本
    cursor.execute("SELECT id, text FROM vectors")
    rows = cursor.fetchall()
    for rowid, text in rows:
        try:
            cursor.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (rowid, text))
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()

def _incremental_update():
    """Incremental update: Compare current file status with file_versions table, re-vectorize and update new/modified files, delete corresponding records from vectors table for deleted files. Also sync memories directory. | 增量更新：对比当前文件状态与 file_versions 表，对新增/修改的文件重新向量化并更新，对删除的文件从 vectors 表中删除对应的记录。同时同步 memories 目录。"""
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
                text = re.sub(r'^<!--.*?-->', '', text, flags=re.DOTALL).strip()
                if not text:
                    continue
                # Delete old records if they exist | 删除旧记录（如果存在）
                cursor.execute("SELECT id FROM vectors WHERE source = ?", (f"file:{path}",))
                old_ids = cursor.fetchall()
                for (old_id,) in old_ids:
                    cursor.execute("DELETE FROM fts WHERE rowid = ?", (old_id,))
                cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
                # Insert new vector | 插入新向量
                model = _get_model()
                emb = model.encode(text)
                emb_blob = emb.tobytes()
                
                # 根据路径判断文档类型
                if "tools" in Path(path).parts:
                    doc_type = "tool"
                elif "skills" in Path(path).parts:
                    doc_type = "skill"
                elif "memories" in Path(path).parts:
                    doc_type = "conversation"
                else:
                    doc_type = "hyw" # What the hell | 何意味
                
                cursor.execute(
                    "INSERT INTO vectors (text, embedding, source, type) VALUES (?, ?, ?, ?)",
                    (text, emb_blob, f"file:{path}", doc_type)
                )
                new_id = cursor.lastrowid
                cursor.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (new_id, text))
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
            cursor.execute("SELECT id FROM vectors WHERE source = ?", (f"file:{path}",))
            old_ids = cursor.fetchall()
            for (old_id,) in old_ids:
                cursor.execute("DELETE FROM fts WHERE rowid = ?", (old_id,))
            cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
            cursor.execute("DELETE FROM file_versions WHERE path = ?", (path,))
            print(f"Deleted: {path} | 已删除: {path}")

    # 3. Sync conversation memories: for each conversation record, check if backup file exists; if not, delete the record. | 同步对话记忆：对于每条对话记录，检查备份文件是否存在；若不存在则删除记录。
    cursor.execute("SELECT id, source FROM vectors WHERE type = 'conversation'")
    conv_records = cursor.fetchall()
    for conv_id, source in conv_records:
        if source:
            backup_path = KNOWLEDGE_ROOT / source
            if not backup_path.exists():
                cursor.execute("DELETE FROM fts WHERE rowid = ?", (conv_id,))
                cursor.execute("DELETE FROM vectors WHERE id = ?", (conv_id,))
                print(f"Deleted orphaned conversation memory: {source} | 删除孤立的对话记忆: {source}")

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
    cursor.execute('DELETE FROM fts')
    conn.commit()
    conn.close()
    # Reinsert all files | 重新插入所有文件
    _incremental_update()
    # Rebuild FTS index just in case | 确保 FTS 索引重建
    _rebuild_fts_index()

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

# 5. Retrieval Interface (Single-shot hybrid search, no recursion) | 检索接口（单次混合搜索，无递归）
def search(query: str, k: int = 5):
    """
    Retrieve the top k knowledge entries most similar to the query (single-shot, no recursion) | 检索与 query 最相似的 k 条知识（单次检索，无递归）
    Return a list of strings (each knowledge entry is plain text) | 返回字符串列表（每条知识为纯文本）
    """
    # Ignore recursive parameters, use single-shot retrieval | 忽略递归参数，直接单次检索
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Also read the type field | 同时读取 type 字段
    cursor.execute("SELECT id, text, embedding, type FROM vectors")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return []

    model = _get_model()
    q_emb = model.encode(query)
    vector_scores = []   # list of (score, id, text, type) | 列表存储 (得分, id, 文本, 类型)
    for doc_id, text, emb_blob, doc_type in rows:
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
        vector_scores.append((final_score, doc_id, text, doc_type))

    # Sort vector scores descending | 向量得分降序排序
    vector_scores.sort(reverse=True, key=lambda x: x[0])

    # Clean FTS query: remove characters that have special meaning in FTS5 query syntax | 清洗 FTS 查询：移除 FTS5 查询语法中有特殊含义的字符
    def clean_fts_query(q: str) -> str:
        # Keep letters, digits, Chinese characters, and spaces; replace everything else with space | 保留字母、数字、中文字符和空格，其余替换为空格
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', q)
        # Collapse multiple spaces | 合并多个空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    # Hybrid search (always enabled) | 混合搜索（始终启用）
    # Perform FTS5 search | 执行 FTS5 搜索
    conn_fts = sqlite3.connect(VECTOR_DB_PATH)
    cursor_fts = conn_fts.cursor()
    # Use BM25 ranking, get top (k * 2) results | 使用 BM25 排序，获取前 (k*2) 条
    fts_query = clean_fts_query(query)
    if fts_query:
        try:
            cursor_fts.execute(
                "SELECT rowid, rank FROM fts WHERE text MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, k * 2)
            )
            fts_results = cursor_fts.fetchall()  # list of (rowid, rank)
        except Exception as e:
            # FTS may fail for other reasons, fallback | FTS 可能因其他原因失败，回退
            print(f"FTS search failed: {e}")
            fts_results = []
    else:
        fts_results = []
    conn_fts.close()

    # Build a map of doc_id -> fts_rank (lower rank is better) | 构建 doc_id -> fts 排名映射
    fts_rank_map = {}
    for rank_idx, (rowid, rank) in enumerate(fts_results):
        fts_rank_map[rowid] = rank_idx + 1  # 1‑based rank

    # Combine scores using RRF (Reciprocal Rank Fusion) | 使用 RRF（倒数排名融合）合并得分
    K = 60  # constant
    combined = {}
    # Vector part | 向量部分
    for idx, (vec_score, doc_id, text, doc_type) in enumerate(vector_scores):
        rank = idx + 1
        rrf_score = _HYBRID_VECTOR_WEIGHT / (K + rank)
        combined[doc_id] = (rrf_score, text, doc_type, vec_score)
    # FTS part | FTS 部分
    for doc_id, fts_rank in fts_rank_map.items():
        rrf_score = _HYBRID_FTS_WEIGHT / (K + fts_rank)
        if doc_id in combined:
            old_score, text, doc_type, vec_score = combined[doc_id]
            combined[doc_id] = (old_score + rrf_score, text, doc_type, vec_score)
        else:
            # Should not happen because all FTS results should be in vectors, but handle gracefully | 不应发生，但优雅处理
            combined[doc_id] = (rrf_score, "", "", 0)

    # Sort by combined score descending | 按合并得分降序排序
    sorted_items = sorted(combined.items(), key=lambda x: x[1][0], reverse=True)
    # Select top k texts | 选择前 k 条文本
    final_texts = [item[1][1] for item in sorted_items[:k] if item[1][1]]
    # If not enough results from hybrid, fallback to vector results | 如果混合结果不足，回退到向量结果
    if len(final_texts) < k:
        final_texts.extend([text for _, _, text, _ in vector_scores if text not in final_texts][:k - len(final_texts)])

    # Return final results directly (no recursion) | 直接返回最终结果（无递归）
    return final_texts

# 6. Dynamically Insert Conversation Memory | 动态插入对话记忆
def add_conversation(user_msg: str, ai_msg: str):
    """
    Dynamically insert a round of Q&A into the vector library (takes effect in real time), and back up to the knowledge/memories/ directory | 将一轮问答动态插入向量库（实时生效），同时备份到 knowledge/memories/ 目录
    """
    text = f"User | 用户: {user_msg}\nAI: {ai_msg}"
    # Generate backup file name with timestamp and hash | 生成带时间戳和哈希的备份文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_filename = f"{timestamp}.md"
    backup_path = MEMORIES_DIR / backup_filename
    # Insert into vector library using backup file path as source | 使用备份文件路径作为 source 插入向量库
    source = str(backup_path.relative_to(KNOWLEDGE_ROOT))
    _add_document(text, source=source, doc_type="conversation")

    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
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