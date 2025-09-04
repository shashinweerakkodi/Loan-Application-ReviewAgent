
from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import math
import re

def _split_chunks(text: str) -> List[Dict]:
    # Split by headings or paragraph breaks
    parts = re.split(r'\n(?=## )', text.strip())
    chunks = []
    for i, p in enumerate(parts):
        title_match = re.match(r'^(## .+)$', p.splitlines()[0])
        title = title_match.group(1) if title_match else f"Section {i+1}"
        chunks.append({"id": f"chunk_{i+1}", "title": title, "text": p.strip()})
    return chunks

def _bow(text: str) -> Dict[str, float]:
    # simple bag of words with term frequency
    tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1.0
    # L2 normalize
    norm = math.sqrt(sum(v*v for v in tf.values())) or 1.0
    for k in tf:
        tf[k] /= norm
    return tf

def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    # dot product
    if len(a) < len(b):
        a, b = b, a
    s = 0.0
    for k, v in b.items():
        if k in a:
            s += a[k] * v
    return s

def search_policy(query: str, policy_path: Path, top_k: int = 3) -> List[Dict]:
    """
    Lightweight local semantic-ish search (no external deps).
    Returns top_k chunks with the highest cosine similarity.
    """
    if not policy_path.exists():
        return []
    text = policy_path.read_text(encoding='utf-8', errors='ignore')
    chunks = _split_chunks(text)
    qv = _bow(query)
    scored = []
    for ch in chunks:
        cv = _bow(ch["text"])
        score = _cosine(qv, cv)
        scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = [dict(ch[1], score=round(ch[0], 3)) for ch in scored[:top_k]]
    return top
