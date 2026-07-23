"""
Vercel Serverless Function entrypoint for bridge-archetypes-100
- Runs FastAPI as ASGI via mangum handler
- SQLite DBs in /tmp/ (read-only filesystem except /tmp)
- Static files served by Vercel CDN (public/ dir)
"""
import os, sys, json, shutil

# Paths: Vercel mounts repo at /var/task/
BASE = os.path.dirname(__file__)
BACKEND = os.path.join(BASE, "..", "backend", "src")
DATA_DIR = "/tmp"  # ONLY writable dir in Vercel functions

sys.path.insert(0, BACKEND)

# Patch DB paths to /tmp/ before importing
os.environ["BRIDGE100_DB_PATH"] = os.path.join(DATA_DIR, "bridge100.db")
os.environ["ONTOLOGY_DB"] = os.path.join(DATA_DIR, "ontology.db")
os.environ["BRIDGE100_LOG"] = "warning"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel
from typing import Literal
import numpy as np

# Inline minimal imports (no agent/ontology for cold-start speed)
from archetypes import REGISTRY, find_by_category, find_by_tag, agent_generate
from db import init_db, seed_bridges, save_simulation, get_sims, sim_count
from ontology import OntologyEngine, seed_ontology

_ontology = None

app = FastAPI(title="bridge-archetypes-100")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()
    seed_bridges(REGISTRY)
    global _ontology
    _ontology = OntologyEngine()
    c = _ontology.db.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
    if c == 0:
        seed_ontology(_ontology)
        c = _ontology.db.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
    print(f"[vercel] Archetypes={len(REGISTRY)}, Ontology={c}")

class SolveReq(BaseModel):
    archetype_id: str = "W01"
    L_mm: float = 4000
    b_mm: float = 300
    h_mm: float = 450
    E_MPa: float = 10000
    fb_MPa: float = 12
    fs_MPa: float = 1.2
    P_N: float = 0
    support: Literal["cantilever", "simple"] = "cantilever"
    grain_amp: float = 8.0

def solve_py(p):
    L, b, h, E = p.L_mm, p.b_mm, p.h_mm, p.E_MPa
    P = p.P_N
    I = b * h**3 / 12
    Z = b * h**2 / 6
    A = b * h
    N = 100
    x = np.linspace(0, L, N)
    if p.support == "cantilever":
        M = P * (L - x)
        delta = P * x**2 * (3*L - x) / (6*E*I)
        Q = np.full_like(x, P)
    else:
        M_left = P * x[x <= L/2] / 2
        M_right = P * (L - x[x > L/2]) / 2
        M = np.concatenate([M_left, M_right])
        delta = np.where(x <= L/2, P*x*(3*L**2-4*x**2)/(48*E*I), P*(L-x)*(3*L**2-4*(L-x)**2)/(48*E*I))
        Q = np.where(x < L/2, P/2, -P/2)
    sigma = M / Z
    tau = 3 * np.abs(Q) / (2 * A)
    vm = np.sqrt(sigma**2 + 3*tau**2)
    sigma_max = float(np.max(sigma))
    tau_max = float(np.max(tau))
    delta_max = float(np.max(delta))
    Mmax = P * L if p.support == "cantilever" else P * L / 4
    h_req = ((6 * Mmax / p.fb_MPa) / b)**(1/3) if P > 0 else h
    grain = p.grain_amp * np.sin(2*np.pi*x/L*3)
    sumo = P / 9.80665 / 150.0
    return {
        "ok": True, "archetype_id": p.archetype_id,
        "sigma_max_MPa": round(sigma_max, 2), "tau_max_MPa": round(tau_max, 3),
        "vm_max_MPa": round(float(np.max(vm)), 2), "delta_max_mm": round(delta_max, 3),
        "sigma_ratio": round(sigma_max/p.fb_MPa, 3), "tau_ratio": round(tau_max/p.fs_MPa, 3),
        "fractured": sigma_max > p.fb_MPa, "required_h_mm": round(h_req, 1),
        "sumo_weight_kg": round(sumo, 2), "x": np.round(x, 1).tolist(),
        "sigma": np.round(sigma, 2).tolist(), "delta": np.round(delta, 3).tolist(),
        "grain_angle": np.round(grain, 1).tolist(), "source": "vercel"
    }

@app.post("/solve")
def solve(req: SolveReq):
    result = solve_py(req)
    save_simulation(req.archetype_id, req.dict(), result)
    return result

@app.get("/archetypes")
def list_arches(category: str = None, tag: str = None):
    arches = REGISTRY
    if category:
        arches = [a for a in arches if a.category == category]
    if tag:
        arches = [a for a in arches if tag in a.tags]
    return [{"id": a.id, "name": a.name, "category": a.category, "tags": list(a.tags)} for a in arches]

@app.get("/archetypes/{arch_id}")
def get_arch(arch_id: str):
    for a in REGISTRY:
        if a.id == arch_id:
            return a.generate()
    return {"error": "not found"}

@app.get("/sims")
def list_sims(fractured: bool = False, limit: int = 20):
    return get_sims(fractured_only=fractured, limit=limit)

@app.get("/ontology/concepts")
def ontology_concepts(search: str = None, category: str = None):
    if not _ontology:
        return {"error": "not initialized"}
    if search:
        return _ontology.search(search, category)
    rows = _ontology.db.execute("SELECT id,label,category,icon FROM concepts WHERE 1=1" + (" AND category=?" if category else ""), [category] if category else []).fetchall()
    return [dict(r) for r in rows]

@app.get("/ontology/concepts/{cid}")
def ontology_concept(cid: str):
    if not _ontology:
        return {"error": "not initialized"}
    return {"concept": _ontology.get_concept(cid), "related": _ontology.related(cid), "explanation": _ontology.explain(cid)}

@app.get("/ontology/path")
def ontology_path(from_id: str, to_id: str, max_depth: int = 4):
    if not _ontology:
        return {"error": "not initialized"}
    paths = _ontology.path(from_id, to_id, max_depth)
    labeled = []
    for p in paths:
        labeled.append([{"id": nid, "label": (_ontology.get_concept(nid) or {}).get("label", nid)} for nid in p])
    return {"paths": labeled}

@app.get("/ontology/quiz")
def ontology_quiz(category: str = None, difficulty: int = None, limit: int = 3):
    if not _ontology:
        return {"error": "not initialized"}
    return _ontology.quiz(category, difficulty, limit)

@app.post("/agent/chat")
def agent_chat(body: dict):
    from agent import StructuralAgent  # lazy import for cold-start
    query = body.get("query", "")
    history = body.get("history", [])
    resp = StructuralAgent().chat(history, query)
    return {"query": query, "thoughts": resp.get("thoughts", []), "answer": resp.get("natural_language", ""), "data": resp.get("result")}

@app.get("/")
def root():
    sim_count_val = sim_count()
    ont_count = _ontology.db.execute("SELECT COUNT(*) FROM concepts").fetchone()[0] if _ontology else 0
    return {"app": "bridge-archetypes-100", "archetypes": len(REGISTRY), "sims": sim_count_val, "ontology_concepts": ont_count, "env": "vercel"}

# Lambda/Serverless handler
handler = Mangum(app, lifespan="off")

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
