# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Knowledge Module - Hybrid Search (Vector + FTS5 + RRF)
"""

import sqlite3
import numpy as np
import re

from .config import VECTOR_DB_PATH, HYBRID_VECTOR_WEIGHT, HYBRID_FTS_WEIGHT, get_model


def search(query: str, k: int = 5):
    """
    Retrieve the top k knowledge entries most similar to the query (single-shot, no recursion)
    Return a list of strings
    """
    conn = sqlite3.connect(VECTOR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, embedding, type FROM vectors")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return []

    model = get_model()
    q_emb = model.encode(query)
    vector_scores = []
    for doc_id, text, emb_blob, doc_type in rows:
        emb = np.frombuffer(emb_blob, dtype=np.float32)
        dot = np.dot(q_emb, emb)
        norm_q = np.linalg.norm(q_emb)
        norm_d = np.linalg.norm(emb)
        sim = dot / (norm_q * norm_d) if norm_q * norm_d != 0 else 0

        if doc_type == 'tool':
            weight = 1.0
        elif doc_type == 'skill':
            weight = 0.8
        elif doc_type == 'conversation':
            weight = 0.2
        else:
            weight = 1.0

        final_score = sim * weight
        vector_scores.append((final_score, doc_id, text, doc_type))

    vector_scores.sort(reverse=True, key=lambda x: x[0])

    def clean_fts_query(q: str) -> str:
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\s]', ' ', q)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    conn_fts = sqlite3.connect(VECTOR_DB_PATH)
    cursor_fts = conn_fts.cursor()
    fts_query = clean_fts_query(query)
    if fts_query:
        try:
            cursor_fts.execute(
                "SELECT rowid, rank FROM fts WHERE text MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, k * 2)
            )
            fts_results = cursor_fts.fetchall()
        except Exception as e:
            print(f"FTS search failed: {e}")
            fts_results = []
    else:
        fts_results = []
    conn_fts.close()

    fts_rank_map = {}
    fts_rowids = []
    for rank_idx, (rowid, rank) in enumerate(fts_results):
        fts_rank_map[rowid] = rank_idx + 1
        fts_rowids.append(rowid)

    # Fetch text and type for FTS-only results
    fts_text_map = {}
    if fts_rowids:
        conn_fts2 = sqlite3.connect(VECTOR_DB_PATH)
        cursor_fts2 = conn_fts2.cursor()
        placeholders = ','.join('?' * len(fts_rowids))
        cursor_fts2.execute(
            f"SELECT id, text, type FROM vectors WHERE id IN ({placeholders})",
            fts_rowids
        )
        for doc_id, text, doc_type in cursor_fts2.fetchall():
            fts_text_map[doc_id] = (text, doc_type)
        conn_fts2.close()

    K = 60
    combined = {}
    for idx, (vec_score, doc_id, text, doc_type) in enumerate(vector_scores):
        rank = idx + 1
        rrf_score = HYBRID_VECTOR_WEIGHT / (K + rank)
        combined[doc_id] = (rrf_score, text, doc_type, vec_score)
    for doc_id, fts_rank in fts_rank_map.items():
        rrf_score = HYBRID_FTS_WEIGHT / (K + fts_rank)
        if doc_id in combined:
            old_score, text, doc_type, vec_score = combined[doc_id]
            combined[doc_id] = (old_score + rrf_score, text, doc_type, vec_score)
        else:
            text, doc_type = fts_text_map.get(doc_id, ("", ""))
            combined[doc_id] = (rrf_score, text, doc_type, 0)

    sorted_items = sorted(combined.items(), key=lambda x: x[1][0], reverse=True)
    final_texts = [item[1][1] for item in sorted_items[:k] if item[1][1]]
    if len(final_texts) < k:
        final_texts.extend([text for _, _, text, _ in vector_scores if text not in final_texts][:k - len(final_texts)])

    return final_texts