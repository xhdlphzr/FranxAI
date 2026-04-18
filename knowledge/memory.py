# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module - Conversation Memory Management
"""

from datetime import datetime

from .config import KNOWLEDGE_ROOT, MEMORIES_DIR
from .vector import add_document


def add_conversation(user_msg: str, ai_msg: str):
    """
    Dynamically insert a round of Q&A into the vector library (takes effect in real time), and back up to the knowledge/memories/ directory
    """
    text = f"User: {user_msg}\nAI: {ai_msg}"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_filename = f"{timestamp}.md"
    backup_path = MEMORIES_DIR / backup_filename
    source = str(backup_path.relative_to(KNOWLEDGE_ROOT))
    add_document(text, source=source, doc_type="conversation")

    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(f"⚠️ Failed to write memory backup: {e}")