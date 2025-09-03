import os
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional

_DB_PATH = None

def init_db(path: str = "agent.db"):
    """Initialize SQLite database if it doesn't exist."""
    global _DB_PATH
    _DB_PATH = path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS case_meta (
                case_id TEXT PRIMARY KEY,
                meta_json TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            )
        """)
        conn.commit()

def _conn():
    if not _DB_PATH:
        raise RuntimeError("DB not initialized. Call init_db(path) first.")
    return sqlite3.connect(_DB_PATH)

def get_or_create_case(case_id: str) -> Dict[str, Any]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, created_at FROM cases WHERE id = ?", (case_id,))
        row = cur.fetchone()
        if row:
            return {"id": row[0], "created_at": row[1]}
        cur.execute("INSERT INTO cases (id, created_at) VALUES (?, ?)", (case_id, time.time()))
        conn.commit()
        return {"id": case_id, "created_at": time.time()}

def list_cases(limit: int = 100) -> List[Dict[str, Any]]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, created_at FROM cases ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [{"id": r[0], "created_at": r[1]} for r in rows]

def save_message(case_id: str, role: str, content: str) -> None:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (case_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                    (case_id, role, content, time.time()))
        conn.commit()

def get_history(case_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT role, content, created_at FROM messages
            WHERE case_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (case_id, limit))
        rows = cur.fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]

def set_case_meta(case_id: str, meta: Dict[str, Any]) -> None:
    payload = json.dumps(meta, ensure_ascii=False)
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("REPLACE INTO case_meta (case_id, meta_json) VALUES (?, ?)", (case_id, payload))
        conn.commit()

def get_case_meta(case_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT meta_json FROM case_meta WHERE case_id = ?", (case_id,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except Exception:
            return None
