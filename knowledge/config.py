# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module - Shared Constants and Model Singleton
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_ROOT = Path(__file__).parent
TOOLS_DIR = KNOWLEDGE_ROOT / 'tools'
MEMORIES_DIR = KNOWLEDGE_ROOT / 'memories'
VECTOR_DB_PATH = KNOWLEDGE_ROOT / "knowledge.db"

# Create memories directory if it does not exist
MEMORIES_DIR.mkdir(parents=True, exist_ok=True)

# Hybrid search weights
HYBRID_VECTOR_WEIGHT = 0.7
HYBRID_FTS_WEIGHT = 0.3

# Global Model (Singleton)
_model = None
MODEL_NAME = 'all-MiniLM-L12-v2'

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model