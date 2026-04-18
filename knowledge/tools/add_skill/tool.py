import time
import sqlite3
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

def execute(name: str, content: str):
    """
    Save a skill as Markdown and immediately index it into the knowledge base.

    Args:
        name: Skill name (used as filename, e.g., "nginx_setup")
        content: Skill content in Markdown format
    """
    # Lazy import to avoid circular dependency at module load time
    from knowledge import _add_document, VECTOR_DB_PATH, KNOWLEDGE_ROOT

    # Sanitize name
    safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-')).strip()
    if not safe_name:
        return "Error: Invalid skill name"

    filename = f"{safe_name}.md"
    filepath = SKILLS_DIR / filename
    relative_path = str(filepath.relative_to(KNOWLEDGE_ROOT))
    source_key = f"file:{relative_path}"

    # Write the file
    filepath.write_text(content, encoding='utf-8')

    # Remove old entries with the same source (handle updates)
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vectors WHERE source = ?", (source_key,))
    old_ids = cursor.fetchall()
    for (old_id,) in old_ids:
        cursor.execute("DELETE FROM fts WHERE rowid = ?", (old_id,))
    cursor.execute("DELETE FROM vectors WHERE source = ?", (source_key,))
    conn.commit()
    conn.close()

    # Add to vector database immediately
    _add_document(content, source=source_key, doc_type="skill")

    # Update file_versions to prevent re-indexing on restart
    mtime = filepath.stat().st_mtime
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO file_versions (path, mtime, last_updated) VALUES (?, ?, ?)",
        (relative_path, mtime, time.time())
    )
    conn.commit()
    conn.close()

    return f"Skill '{safe_name}' saved and indexed successfully."