# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module - Vector Database Operations
"""

import sqlite3
import numpy as np
import time
import re
from pathlib import Path

from .config import KNOWLEDGE_ROOT, VECTOR_DB_PATH, get_model


def get_file_state():
    """Get the status of all current .md files (path -> mtime)"""
    state = {}
    for md_file in KNOWLEDGE_ROOT.rglob("*.md"):
        try:
            mtime = md_file.stat().st_mtime
            state[str(md_file.relative_to(KNOWLEDGE_ROOT))] = mtime
        except Exception as e:
            print(f"⚠️ Failed to get file status {md_file}: {e}")
    return state


def add_document(text: str, source: str = "", doc_type: str = "generic"):
    """Insert document directly (no rebuild)"""
    model = get_model()
    emb = model.encode(text)
    emb_blob = emb.tobytes()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vectors WHERE text = ?", (text,))
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO vectors (text, embedding, source, type) VALUES (?, ?, ?, ?)",
            (text, emb_blob, source, doc_type)
        )
        new_id = cursor.lastrowid
        try:
            cursor.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (new_id, text))
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e):
                raise
        conn.commit()
    conn.close()


def init_vector_db():
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
    try:
        cursor.execute("ALTER TABLE vectors ADD COLUMN source TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE vectors ADD COLUMN type TEXT")
    except sqlite3.OperationalError:
        pass
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
            text,
            tokenize = 'unicode61'
        )
    ''')
    conn.commit()
    conn.close()


def rebuild_fts_index():
    """Rebuild the FTS index from the vectors table"""
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fts")
    cursor.execute("SELECT id, text FROM vectors")
    rows = cursor.fetchall()
    for rowid, text in rows:
        try:
            cursor.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (rowid, text))
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def incremental_update():
    """Incremental update: re-vectorize new/modified files, delete removed files"""
    print("Performing incremental vector library update...")
    current_state = get_file_state()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT path, mtime FROM file_versions")
    stored = {row[0]: row[1] for row in cursor.fetchall()}

    # 1. Process new or modified files
    for path, mtime in current_state.items():
        if path not in stored or stored[path] != mtime:
            file_path = KNOWLEDGE_ROOT / path
            try:
                text = file_path.read_text(encoding='utf-8').strip()
                text = re.sub(r'^<!--.*?-->', '', text, flags=re.DOTALL).strip()
                if not text:
                    continue
                cursor.execute("SELECT id FROM vectors WHERE source = ?", (f"file:{path}",))
                old_ids = cursor.fetchall()
                for (old_id,) in old_ids:
                    cursor.execute("DELETE FROM fts WHERE rowid = ?", (old_id,))
                cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
                model = get_model()
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
                cursor.execute(
                    "INSERT OR REPLACE INTO file_versions (path, mtime, last_updated) VALUES (?, ?, ?)",
                    (path, mtime, time.time())
                )
                print(f"Updated: {path}")
            except Exception as e:
                print(f"⚠️ Failed to update file {path}:")

    # 2. Process deleted files
    for path in stored:
        if path not in current_state:
            cursor.execute("SELECT id FROM vectors WHERE source = ?", (f"file:{path}",))
            old_ids = cursor.fetchall()
            for (old_id,) in old_ids:
                cursor.execute("DELETE FROM fts WHERE rowid = ?", (old_id,))
            cursor.execute("DELETE FROM vectors WHERE source = ?", (f"file:{path}",))
            cursor.execute("DELETE FROM file_versions WHERE path = ?", (path,))
            print(f"Deleted: {path}")

    # 3. Sync conversation memories
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


def full_rebuild():
    """Full rebuild (for first run or complete reset)"""
    print("Performing full vector library rebuild...")
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM vectors')
    cursor.execute('DELETE FROM file_versions')
    cursor.execute('DELETE FROM fts')
    conn.commit()
    conn.close()
    incremental_update()
    rebuild_fts_index()


def check_and_update():
    """Initialize DB and check if full rebuild is needed"""
    init_vector_db()
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vectors")
    count = cursor.fetchone()[0]
    conn.close()
    if count == 0:
        full_rebuild()
    else:
        incremental_update()