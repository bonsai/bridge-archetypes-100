"""
bridge-archetypes-100: Unified FastAPI Backend
Integrates: archetypes, DB, Haskell solver (optional), existing wood FEM
"""
import os, sys, json, subprocess, shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Optional
import numpy as np

from archetypes import REGISTRY, find_by_category, find_by_tag, agent_generate, generate_batch
from db import init_db, seed_bridges, save_simulation, get_sims, sim_count
from agent import StructuralAgent
from ontology import OntologyEngine, init_ontology_db, seed_ontology

_struct_agent = StructuralAgent()
_ontology = None

app = FastAPI(title="bridge-archetypes-100")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Static files (frontend)
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static")
if not os.path.exists(static_dir):
    static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"[bridge100] Serving static from: {static_dir}")

# ============================================================
# Startup
# ============================================================
@app.on_event("startup")
def startup():
    init_db()
    seed_bridges(REGISTRY)
    global _ontology
    db_file = os.environ.get("ONTOLOGY_DB", "/home/bons/repos/bridge-archetypes-100/data/ontology.db")
    os.makedirs(os.path.dirname(db_file), exist_ok=True)
    _ontology = OntologyEngine(db_file)
    c = _ontology.db.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
    if c == 0:
        seed_ontology(_ontology)
        c = _ontology.db.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
    print(f"[bridge100] Archetypes={len(REGISTRY)}, Sims={sim_count()}, OntologyConcepts={c}")

@app.on_event("shutdown")
def shutdown():
    global _ontology
    if _ontology:
        _ontology.close()
        _ontology = None

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
    use_haskell: bool = False
    ortho_factor: float = 1.0
    grain_amp: float = 8.0

class SolveResp(BaseModel):
    ok: bool
    archetype_id: str
    sigma_max_MPa: float
    tau_max_MPa: float
    vm_max_MPa: float
    delta_max_mm: float
    sigma_ratio: float
    tau_ratio: float
    fractured: bool
    required_h_mm: float
    sumo_weight_kg: float
    x: list[float]
    sigma: list[float]
    delta: list[float]
    grain_angle: list[float]
    source: str = "python"

# ============================================================
# Solve (Python analytical)
# ============================================================
def solve_py(p: SolveReq) -> dict:
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
        delta = np.where(
            x <= L/2,
            P * x * (3*L**2 - 4*x**2) / (48*E*I),
            P * (L - x) * (3*L**2 - 4*(L-x)**2) / (48*E*I)
        )
        Q = np.where(x < L/2, P/2, -P/2)

    sigma = M / Z
    tau = 3 * np.abs(Q) / (2 * A)
    vm = np.sqrt(sigma**2 + 3*tau**2)
    sigma_max = float(np.max(sigma))
    tau_max = float(np.max(tau))
    delta_max = float(np.max(delta))

    if P > 0:
        Mmax = P * L if p.support == "cantilever" else P * L / 4
        h_req = ((6 * Mmax / p.fb_MPa) / b)**(1/3)
    else:
        h_req = h

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
        "grain_angle": np.round(grain, 1).tolist(), "source": "python"
    }

# ============================================================
# Haskell solver (json pipe)
# ============================================================
HASKELL_BIN = os.environ.get("BRIDGE100_HASKELL", "/home/bons/repos/bridge-archetypes-100/haskell/dist/bridge100-solver")

def solve_haskell(p: SolveReq) -> Optional[dict]:
    if not shutil.which(HASKELL_BIN) and not os.path.exists(HASKELL_BIN):
        return None
    inp = {
        "l_mm": p.L_mm, "b_mm": p.b_mm, "h_mm": p.h_mm,
        "e1_MPa": p.E_MPa, "e2_MPa": p.E_MPa*0.1, "nu12": 0.35,
        "g12_MPa": p.E_MPa*0.06, "theta_deg": p.grain_amp,
        "p_N": p.P_N, "fb_MPa": p.fb_MPa, "support": p.support
    }
    try:
        proc = subprocess.run(
            [HASKELL_BIN],
            input=json.dumps(inp).encode(),
            capture_output=True, timeout=5
        )
        if proc.returncode == 0:
            return json.loads(proc.stdout)
    except Exception:
        pass
    return None

# ============================================================
# Endpoints
# ============================================================

@app.post("/solve", response_model=SolveResp)
def solve(req: SolveReq):
    if req.use_haskell:
        h = solve_haskell(req)
        if h:
            return {**h, "source": "haskell"}
    result = solve_py(req)
    # persist
    save_simulation(req.archetype_id, req.dict(), result)
    return result

@app.get("/archetypes")
def list_arches(category: str = None, tag: str = None):
    arches = REGISTRY
    if category:
        arches = [a for a in arches if a.category == category]
    if tag:
        arches = [a for a in arches if tag in a.tags]
    return [{"id": a.id, "name": a.name, "category": a.category,
             "tags": list(a.tags)} for a in arches]

@app.get("/archetypes/{arch_id}")
def get_arch(arch_id: str):
    for a in REGISTRY:
        if a.id == arch_id:
            return a.generate()
    return {"error": "not found"}

@app.post("/generate")
def gen_archetype(category: str, count: int = 1, constraints: dict = None):
    results = []
    for _ in range(count):
        draft = agent_generate(category, constraints or {})
        results.append(draft)
    return results

@app.get("/sims")
def list_sims(fractured: bool = False, limit: int = 20):
    return get_sims(fractured_only=fractured, limit=limit)

@app.get("/ontology/concepts")
def ontology_concepts(search: str = None, category: str = None):
    if not _ontology:
        return {"error": "ontology not initialized"}
    if search:
        return _ontology.search(search, category)
    rows = _ontology.db.execute("SELECT id,label,category,icon FROM concepts WHERE 1=1" + (" AND category=?" if category else ""), [category] if category else []).fetchall()
    return [dict(r) for r in rows]

@app.get("/ontology/concepts/{cid}")
def ontology_concept(cid: str):
    if not _ontology:
        return {"error": "ontology not initialized"}
    return {
        "concept": _ontology.get_concept(cid),
        "related": _ontology.related(cid),
        "explanation": _ontology.explain(cid),
    }

@app.get("/ontology/path")
def ontology_path(from_id: str, to_id: str, max_depth: int = 4):
    if not _ontology:
        return {"error": "ontology not initialized"}
    paths = _ontology.path(from_id, to_id, max_depth)
    # Convert ids to labels
    labeled = []
    for p in paths:
        labeled.append([{"id": nid, "label": (_ontology.get_concept(nid) or {}).get("label", nid)} for nid in p])
    return {"paths": labeled}

@app.get("/ontology/quiz")
def ontology_quiz(category: str = None, difficulty: int = None, limit: int = 3):
    if not _ontology:
        return {"error": "ontology not initialized"}
    return _ontology.quiz(category, difficulty, limit)

@app.post("/agent/chat")
def agent_chat(body: dict):
    query = body.get("query", "")
    history = body.get("history", [])
    resp = _struct_agent.chat(history, query)
    return {
        "query": query,
        "thoughts": resp.get("thoughts", []),
        "answer": resp.get("natural_language", ""),
        "data": resp.get("result"),
    }

@app.get("/")
def root():
    sim_count_val = sim_count()
    ont_count = _ontology.db.execute("SELECT COUNT(*) FROM concepts").fetchone()[0] if _ontology else 0
    return {"app": "bridge-archetypes-100", "archetypes": len(REGISTRY), "sims": sim_count_val, "ontology_concepts": ont_count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
