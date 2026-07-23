"""
bridge-archetypes-100: SQLite persistence layer
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = os.environ.get("BRIDGE100_DB", "/home/bons/repos/bridge-archetypes-100/data/bridge100.db")

def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Try multiple possible paths for schema.sql
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "sql", "schema.sql"),
        os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql"),
        os.path.join(os.path.dirname(__file__), "sql", "schema.sql"),
    ]
    schema_path = None
    for c in candidates:
        if os.path.exists(c):
            schema_path = c
            break
    if schema_path:
        with open(schema_path) as f:
            conn.executescript(f.read())
    else:
        print(f"[db] WARNING: schema.sql not found. Tried: {candidates}")
    conn.commit()
    conn.close()

def seed_bridges(archetypes: List):
    """Seed archetypes into bridges table."""
    conn = get_conn()
    for arch in archetypes:
        params = {
            k: getattr(arch, k) for k in ["domains", "tags"]
            if hasattr(arch, k)
        }
        params["domains"] = arch.domains if hasattr(arch, "domains") else {}
        params["tags"] = list(arch.tags) if hasattr(arch, "tags") else []
        conn.execute(
            "INSERT OR REPLACE INTO bridges (id, category, name, params_json) VALUES (?, ?, ?, ?)",
            (arch.id, arch.category, arch.name, json.dumps(params, ensure_ascii=False))
        )
    conn.commit()
    conn.close()

def save_simulation(bridge_id: str, params: Dict, results: Dict) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO simulations (bridge_id, params_json, results_json, sigma_ratio, fractured) VALUES (?, ?, ?, ?, ?)",
        (bridge_id, json.dumps(params), json.dumps(results),
         results.get("sigma_ratio", 0), results.get("fractured", False))
    )
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid

def get_sims(fractured_only: bool = False, limit: int = 50) -> List[Dict]:
    conn = get_conn()
    sql = "SELECT * FROM simulations WHERE 1=1"
    params = []
    if fractured_only:
        sql += " AND fractured = 1"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Convenience
def sim_count() -> int:
    conn = get_conn()
    c = conn.execute("SELECT COUNT(*) FROM simulations").fetchone()[0]
    conn.close()
    return c
