# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module: Unified tool loading + MCP management + Automatic vector knowledge base construction (supports incremental updates)
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

# Add project root directory to sys.path for importing src.mcps
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcps import MCPStdioClient

# Global Model (Singleton)
_model = None
MODEL_NAME = 'all-MiniLM-L12-v2'

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

# Hybrid search is always enabled (weights: vector 0.7, fts 0.3)
_HYBRID_VECTOR_WEIGHT = 0.7
_HYBRID_FTS_WEIGHT = 0.3

# 1. Load Built-in Tools
KNOWLEDGE_ROOT = Path(__file__).parent
TOOLS_DIR = KNOWLEDGE_ROOT / 'tools'
MEMORIES_DIR = KNOWLEDGE_ROOT / 'memories'   # Conversation memory backup directory

# Create memories directory if it does not exist
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

_internal_tools = {}
for item in TOOLS_DIR.iterdir():
    if not item.is_dir() or item.name.startswith('__'):
        continue
    tool_name = item.name
    tool_path = item / 'tool.py'
    readme_path = item / 'README.md'

    if not (tool_path.exists() and readme_path.exists()):
        print(f"⚠️ Tool {tool_name} is missing tool.py or README.md, skipping")
        continue

    try:
        spec = importlib.util.spec_from_file_location(f"knowledge.tools.{tool_name}", tool_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"knowledge.tools.{tool_name}"] = module
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"⚠️ Failed to import tool.py for {tool_name}: {e}, skipping")
        continue

    if not hasattr(module, 'execute'):
        print(f"⚠️ tool.py for {tool_name} does not define execute function, skipping")
        continue

    _internal_tools[tool_name] = module.execute

# 2. Collect All Markdown Files (including memories directory)
def _get_file_state():
    """Get the status of all current .md files (path -> mtime)"""
    state = {}
    for md_file in KNOWLEDGE_ROOT.rglob("*.md"):
        try:
            mtime = md_file.stat().st_mtime
            state[str(md_file.relative_to(KNOWLEDGE_ROOT))] = mtime
        except Exception as e:
            print(f"⚠️ Failed to get file status {md_file}: {e}")
    return state

# 3. MCP Server Management
_mcp_tools = {}
_mcp_clients = []
_mcp_lock = threading.Lock()

def _load_mcp_servers():
    """Load and start MCP servers from config file, add tool descriptions to knowledge base (dynamic addition)"""
    global _mcp_tools
    config_path = PROJECT_ROOT / "config.json"
    if not config_path.exists():
        return
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Failed to read config file: {e}")
        return

    servers = config.get("mcp_servers", [])
    if not servers:
        return

    for server in servers:
        name = server.get("name", "unknown")
        command = server.get("command")
        if not command:
            print(f"Skipping {name}: missing command")
            continue
        args = server.get("args", [])

        try:
            client = MCPStdioClient(command, args)
            client.start()
            time.sleep(0.5)  # Wait for subprocess to be ready
            raw_tools = client.list_tools()
            if not raw_tools:
                print(f"⚠️ {name} returned no tools, skipping")
                client.close()
                continue

            print(f"Connected to MCP server {name}, found {len(raw_tools)} tools")
            _mcp_clients.append(client)
            with _mcp_lock:
                for tool in raw_tools:
                    tool_name = tool["name"]
                    full_name = f"{name}/{tool_name}"
                    description = tool.get("description", "")
                    params = tool.get("inputSchema", {}).get("properties", {})
                    param_str = ", ".join([f"{k} ({v.get('type','any')})" for k, v in params.items()])

                    # Create wrapper function
                    def make_wrapper(mcp_client, t_name):
                        def wrapper(**kwargs):
                            try:
                                return mcp_client.call_tool(t_name, kwargs)
                            except Exception as e:
                                return f"Call failed: {e}"
                        return wrapper
                    _mcp_tools[full_name] = make_wrapper(client, tool_name)
        except Exception as e:
            print(f"Failed to start MCP server {name}: {e}")
            import traceback
            traceback.print_exc()
            continue

# Helper function: Insert a single document into the vector library and FTS index
def _add_document(text: str, source: str = "", doc_type: str = "generic"):
    """Insert document directly (no rebuild)"""
    model = _get_model()
    emb = model.encode(text)
    emb_blob = emb.tobytes()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Check if the same text already exists (optional, avoid duplicates)
    cursor.execute("SELECT id FROM vectors WHERE text = ?", (text,))
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO vectors (text, embedding, source, type) VALUES (?, ?, ?, ?)",
            (text, emb_blob, source, doc_type)
        )
        # Get the newly inserted rowid
        new_id = cursor.lastrowid
        # Also insert into FTS table
        try:
            cursor.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (new_id, text))
        except sqlite3.OperationalError as e:
            # FTS table may not exist yet (first run), ignore
            if "no such table" not in str(e):
                raise
        conn.commit()
    conn.close()

# Start MCP servers (they will call _add_document to dynamically add descriptions)
_load_mcp_servers()

# 4. Vector Library Incremental Update
VECTOR_DB_PATH = KNOWLEDGE_ROOT / "knowledge.db"

def _init_vector_db():
    """Create database tables if they do not exist, and add missing columns"""
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
    # Add missing columns if they do not exist
    try:
        cursor.execute("ALTER TABLE vectors ADD COLUMN source TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        cursor.execute("ALTER TABLE vectors ADD COLUMN type TEXT")
    except sqlite3.OperationalError:
        pass
    # Create FTS5 virtual table for hybrid search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
            text,
            tokenize = 'unicode61'
        )
    ''')
    conn.commit()
    conn.close()

def _rebuild_fts_index():
    """Rebuild the FTS index from the vectors table"""
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Delete all existing FTS entries
    cursor.execute("DELETE FROM fts")
    # Insert all texts from vectors table
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
    """Incremental update: Compare current file status with file_versions table, re-vectorize and update new/modified files, delete corresponding records from vectors table for deleted files. Also sync memories directory."""
    print("Performing incremental vector library update...")
    current_state = _get_file_state()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Get stored file status
    cursor.execute("SELECT path, mtime FROM file_versions")
    stored = {row[0]: row[1] for row in cursor.fetchall()}

    # 1. Process new or modified files
    for path, mtime in current_state.items():
        if path not in stored or stored[path] != mtime:
            # Needs update
            file_path = KNOWLEDGE_ROOT / path
            try:
                text = file_path.read_text(encoding='utf-8').strip()
                text = re.sub(r'^<!--.*?-->', '', text, flags=re.DOTALL).strip()
                if not text:
                    continue
                # Delete old records if they exist
                cursor.execute("SELECT id FROM vectors WHERE source = ?", (f"file:{path}",))
                old_ids = cursor.fetchall()
                for (old_id,) in old_ids:
                    cursor.execute("DELETE FROM fts WHERE rowid = ?", (old_id,))
                cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
                # Insert new vector
                model = _get_model()
                emb = model.encode(text)
                emb_blob = emb.tobytes()
                
                if "tools" in Path(path).parts:
                    doc_type = "tool"
                elif "skills" in Path(path).parts:
                    doc_type = "skill"
                elif "memories" in Path(path).parts:
                    doc_type = "conversation"
                else:
                    doc_type = "hyw"
                
                cursor.execute(
                    "INSERT INTO vectors (text, embedding, source, type) VALUES (?, ?, ?, ?)",
                    (text, emb_blob, f"file:{path}", doc_type)
                )
                new_id = cursor.lastrowid
                cursor.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (new_id, text))
                # Update file_versions table
                cursor.execute(
                    "INSERT OR REPLACE INTO file_versions (path, mtime, last_updated) VALUES (?, ?, ?)",
                    (path, mtime, time.time())
                )
                print(f"Updated: {path}")
            except Exception as e:
                print(f"⚠️ Failed to update file {path}:")

    # 2. Process deleted files (not in current_state but exist in stored)
    for path in stored:
        if path not in current_state:
            cursor.execute("SELECT id FROM vectors WHERE source = ?", (f"file:{path}",))
            old_ids = cursor.fetchall()
            for (old_id,) in old_ids:
                cursor.execute("DELETE FROM fts WHERE rowid = ?", (old_id,))
            cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
            cursor.execute("DELETE FROM file_versions WHERE path = ?", (path,))
            print(f"Deleted: {path}")

    # 3. Sync conversation memories: for each conversation record, check if backup file exists; if not, delete the record.
    cursor.execute("SELECT id, source FROM vectors WHERE type = 'conversation'")
    conv_records = cursor.fetchall()
    for conv_id, source in conv_records:
        if source:
            backup_path = KNOWLEDGE_ROOT / source
            if not backup_path.exists():
                cursor.execute("DELETE FROM fts WHERE rowid = ?", (conv_id,))
                cursor.execute("DELETE FROM vectors WHERE id = ?", (conv_id,))
                print(f"Deleted orphaned conversation memory: {source}")

    conn.commit()
    conn.close()
    print("Incremental update completed.")

def _full_rebuild():
    """Full rebuild (for first run or complete reset)"""
    print("Performing full vector library rebuild...")
    # Clear all tables
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vectors')
    cursor.execute('DELETE FROM file_versions')
    cursor.execute('DELETE FROM fts')
    conn.commit()
    conn.close()
    # Reinsert all files
    _incremental_update()
    # Rebuild FTS index just in case
    _rebuild_fts_index()

# Initialize database   
_init_vector_db()

# Check if first build is needed: If vectors table is empty, full rebuild; else incremental update  
conn = sqlite3.connect(VECTOR_DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM vectors")
count = cursor.fetchone()[0]
conn.close()
if count == 0:
    _full_rebuild()
else:
    _incremental_update()

# 5. Retrieval Interface (Single-shot hybrid search, no recursion)  
def search(query: str, k: int = 5):
    """
    Retrieve the top k knowledge entries most similar to the query (single-shot, no recursion)  
    Return a list of strings (each knowledge entry is plain text) 
    """
    # Ignore recursive parameters, use single-shot retrieval
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    # Also read the type field
    cursor.execute("SELECT id, text, embedding, type FROM vectors")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return []

    model = _get_model()
    q_emb = model.encode(query)
    vector_scores = []   # list of (score, id, text, type)
    for doc_id, text, emb_blob, doc_type in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        dot = np.dot(q_emb, emb)
        norm_q = np.linalg.norm(q_emb)
        norm_d = np.linalg.norm(emb)
        sim = dot / (norm_q * norm_d) if norm_q * norm_d != 0 else 0

        # Apply type weights: tool=1.0, skill=0.8, conversation=0.2, default=1.0
        if doc_type == 'tool':
            weight = 1.0
        elif doc_type == 'skill':
            weight = 0.8
        elif doc_type == 'conversation':
            weight = 0.2
        else:
            weight = 1.0  # Default for mcp or unknown types

        final_score = sim * weight
        vector_scores.append((final_score, doc_id, text, doc_type))

    # Sort vector scores descending
    vector_scores.sort(reverse=True, key=lambda x: x[0])

    # Clean FTS query: remove characters that have special meaning in FTS5 query syntax
    def clean_fts_query(q: str) -> str:
        # Keep letters, digits, Chinese characters, and spaces; replace everything else with space
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', q)
        # Collapse multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    # Hybrid search (always enabled)
    # Perform FTS5 search
    conn_fts = sqlite3.connect(VECTOR_DB_PATH)
    cursor_fts = conn_fts.cursor()
    # Use BM25 ranking, get top (k * 2) results
    fts_query = clean_fts_query(query)
    if fts_query:
        try:
            cursor_fts.execute(
                "SELECT rowid, rank FROM fts WHERE text MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, k * 2)
            )
            fts_results = cursor_fts.fetchall()  # list of (rowid, rank)
        except Exception as e:
            # FTS may fail for other reasons, fallback
            print(f"FTS search failed: {e}")
            fts_results = []
    else:
        fts_results = []
    conn_fts.close()

    # Build a map of doc_id -> fts_rank (lower rank is better)
    fts_rank_map = {}
    for rank_idx, (rowid, rank) in enumerate(fts_results):
        fts_rank_map[rowid] = rank_idx + 1  # 1‑based rank

    # Combine scores using RRF (Reciprocal Rank Fusion)
    K = 60  # constant
    combined = {}
    # Vector part
    for idx, (vec_score, doc_id, text, doc_type) in enumerate(vector_scores):
        rank = idx + 1
        rrf_score = _HYBRID_VECTOR_WEIGHT / (K + rank)
        combined[doc_id] = (rrf_score, text, doc_type, vec_score)
    # FTS part
    for doc_id, fts_rank in fts_rank_map.items():
        rrf_score = _HYBRID_FTS_WEIGHT / (K + fts_rank)
        if doc_id in combined:
            old_score, text, doc_type, vec_score = combined[doc_id]
            combined[doc_id] = (old_score + rrf_score, text, doc_type, vec_score)
        else:
            # Should not happen because all FTS results should be in vectors, but handle gracefully
            combined[doc_id] = (rrf_score, "", "", 0)

    # Sort by combined score descending
    sorted_items = sorted(combined.items(), key=lambda x: x[1][0], reverse=True)
    # Select top k texts
    final_texts = [item[1][1] for item in sorted_items[:k] if item[1][1]]
    # If not enough results from hybrid, fallback to vector results
    if len(final_texts) < k:
        final_texts.extend([text for _, _, text, _ in vector_scores if text not in final_texts][:k - len(final_texts)])

    # Return final results directly (no recursion)
    return final_texts

# 6. Dynamically Insert Conversation Memory
def add_conversation(user_msg: str, ai_msg: str):
    """
    Dynamically insert a round of Q&A into the vector library (takes effect in real time), and back up to the knowledge/memories/ directory
    """
    text = f"User: {user_msg}\nAI: {ai_msg}"
    # Generate backup file name with timestamp and hash
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_filename = f"{timestamp}.md"
    backup_path = MEMORIES_DIR / backup_filename
    # Insert into vector library using backup file path as source
    source = str(backup_path.relative_to(KNOWLEDGE_ROOT))
    _add_document(text, source=source, doc_type="conversation")

    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"⚠️ Failed to write memory backup: {e}")

# 7. Unified Tool Call (Built-in + MCP)
def tools(tool_name: str, arguments: dict = None) -> str:
    """
    Unified tool call interface: Supports built-in tools and MCP tools (format: server_name/tool_name)
    """
    # First check if it is an MCP tool
    if '/' in tool_name:
        with _mcp_lock:
            if tool_name in _mcp_tools:
                try:
                    return _mcp_tools[tool_name](**(arguments or {}))
                except Exception as e:
                    return f"MCP tool call failed: {e}"
            else:
                return f"Error: Unknown MCP tool {tool_name}"
    # Otherwise try built-in tools
    if tool_name not in _internal_tools:
        return f"Error: Unknown tool {tool_name}"
    try:
        return _internal_tools[tool_name](**(arguments or {}))
    except Exception as e:
        return f"Call failed: {e}"

# Export tool function dictionary (only one tools function)
tool_functions = {"tools": tools}

# Tool metadata (description)
tools_metadata = [
    {
        "type": "function",
        "function": {
            "name": "tools",
            "description": "Call any available tool. Parameters: tool_name (tool name), arguments (JSON object). All built-in tools are called through this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Tool name, e.g., read, write, command, search, similarity, add_task, del_task, ett, beijing_subway, etc. External MCP tools use the format server_name/tool_name."
                    },
                    "arguments": {
                        "type": "object",
                        "description": "Tool parameters"
                    }
                },
                "required": ["tool_name"]
            }
        }
    }
]

# Cleanup function (for external calls, e.g., atexit)
def cleanup_mcp_clients():
    """Close all MCP clients"""
    for client in _mcp_clients:
        try:
            client.close()
        except:
            pass

print("Built-in tool list:", list(_internal_tools.keys()))
print(f"MCP tool count：{len(_mcp_tools)}")
print("Knowledge base incremental update completed.")

__all__ = ['tools_metadata', 'tool_functions', 'search', 'cleanup_mcp_clients', 'add_conversation']