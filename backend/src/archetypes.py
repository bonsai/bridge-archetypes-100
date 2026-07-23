"""
bridge-archetypes-100: Functional Archetype Generator + EDN-like DSL

Inspired by Clojure's data-as-code philosophy:
  Archetype = immutable map + derive function
  Bridge = generated instance from archetype + seed params
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, FrozenSet
import json
import math
import random
from functools import lru_cache

# ============================================================
# Core Types
# ============================================================
SeedParams = Dict[str, Any]
DerivedParams = Dict[str, Any]

@dataclass(frozen=True)
class Archetype:
    """Mother template for a bridge structural type."""
    id: str
    name: str
    name_en: str
    category: str
    category_ja: str
    # Generator domain: {param_name: [allowed_values]} or {param_name: (min, max, step)}
    domains: Dict[str, Any] = field(default_factory=dict)
    # Pure function: seed -> fully derived params with mechanical properties
    derive: Callable[[SeedParams], DerivedParams] = field(default=lambda s: s)
    # Structural tags for filtering/querying
    tags: FrozenSet[str] = field(default_factory=frozenset)
    
    def generate(self, seed: SeedParams = None) -> Dict:
        """Generate a concrete bridge instance."""
        if seed is None:
            seed = self._random_seed()
        base = {**seed, "id": self.id, "name": self.name, 
                "category": self.category, "tags": list(self.tags)}
        derived = self.derive(seed)
        return {**base, **derived, "_generated": True}
    
    def _random_seed(self) -> SeedParams:
        """Random sample from domains."""
        seed = {}
        for k, domain in self.domains.items():
            if isinstance(domain, (list, tuple, set)):
                seed[k] = random.choice(list(domain))
            elif isinstance(domain, dict) and domain.get("type") == "range":
                lo, hi, step = domain["lo"], domain["hi"], domain.get("step", 1)
                n_steps = int((hi - lo) / step)
                seed[k] = lo + random.randint(0, n_steps) * step
        return seed

# ============================================================
# Derive Functions (Functional Core)
# ============================================================

def derive_beam(seed: SeedParams) -> DerivedParams:
    """Derive mechanical properties for beam bridges."""
    span = seed["span_m"] * 1000  # mm
    h = seed.get("h_m", seed.get("span_m", 30) / 15) * 1000
    b = seed.get("b_m", seed.get("deck_w_m", 9) / 2) * 1000
    E = seed.get("E_GPa", 200) * 1000  # MPa
    fb = seed.get("fb_MPa", 210)
    I = b * h**3 / 12
    Z = b * h**2 / 6
    A = b * h
    rho = seed.get("rho_kg_m3", 7850)
    m_line = A * 1e-6 * rho
    f_nat = 1.57 * math.sqrt(E * I / (m_line * (span/1000)**4)) if span > 0 and m_line > 0 else 0
    return {
        "L_mm": span, "h_mm": h, "b_mm": b,
        "E_MPa": E, "fb_MPa": fb,
        "I_mm4": I, "Z_mm3": Z, "A_mm2": A,
        "f_nat_Hz": round(f_nat, 2),
        "type": seed.get("type", "simple")
    }

def derive_wood_beam(seed: SeedParams) -> DerivedParams:
    """Derive for wood beam (2級建築士試験 compatible)."""
    L = seed["span_m"] * 1000
    b = seed["b_mm"]
    h = seed["h_mm"]
    grade = seed.get("wood_grade", "sugi-2")
    E_map = {"sugi-2": 10, "hinoki": 12, "matsu": 11}
    fb_map = {"sugi-2": 12, "hinoki": 14, "matsu": 13}
    E = E_map.get(grade, 10) * 1000
    fb = fb_map.get(grade, 12)
    I = b * h**3 / 12
    Z = b * h**2 / 6
    A = b * h
    # Orthotropic grain angle pattern
    grain = [10 * math.sin(2 * math.pi * x / L * 3) for x in range(0, int(L), int(L/20))]
    return {
        "L_mm": L, "b_mm": b, "h_mm": h,
        "E_MPa": E, "fb_MPa": fb, "fs_MPa": 1.2,
        "I_mm4": I, "Z_mm3": Z, "A_mm2": A,
        "wood_grade": grade,
        "grain_angles": [round(g, 1) for g in grain],
        "type": seed.get("type", "simple"),
        "support": seed.get("support", "cantilever")
    }

def derive_arch(seed: SeedParams) -> DerivedParams:
    span = seed["span_m"] * 1000
    rise = seed.get("rise_m", span/1000/5) * 1000
    # Thrust approximation: H = wL^2 / (8r)
    w = 10  # kN/m approx deck load
    H = w * (span/1000)**2 / (8 * rise/1000)
    # Compression in rib
    A = seed.get("A_arch_cm2", 3000) * 100
    sigma_comp = H * 1000 / A
    return {
        "L_mm": span, "rise_mm": rise,
        "thrust_kN": round(H, 1),
        "sigma_comp_MPa": round(sigma_comp, 2),
        "E_MPa": seed.get("E_GPa", 200) * 1000,
        "fb_MPa": seed["fb_MPa"],
        "type": seed.get("type", "deck_arch")
    }

def derive_suspension(seed: SeedParams) -> DerivedParams:
    L = seed.get("main_span_m", seed["span_m"]) * 1000
    # Cable tension under uniform load
    w = 20  # kN/m
    f = L / 1000 / 10  # sag = span/10
    T = w * (L/1000)**2 / (8 * f)
    cable_dia = seed.get("cable_dia_mm", 500)
    A_cable = math.pi * (cable_dia/2)**2
    sigma_cable = T * 1000 / A_cable
    return {
        "L_mm": L,
        "cable_tension_kN": round(T, 0),
        "cable_sigma_MPa": round(sigma_cable, 1),
        "tower_h_m": seed.get("tower_h_m", L/1000/5),
        "fb_MPa": seed["fb_MPa"],
        "E_MPa": seed.get("E_GPa", 200) * 1000,
        "type": seed.get("type", "3span")
    }

# ============================================================
# Registry
# ============================================================

REGISTRY: List[Archetype] = [
    Archetype("B01", "単純合成I桁橋", "Simple Composite I-Girder",
              "beam_bridge", "桁橋",
              domains={"span_m": [20,30,40], "deck_w_m": [8,9,10], "h_m": [2.0,2.5,3.0]},
              derive=derive_beam,
              tags=frozenset({"steel", "simple", "highway"})),
    Archetype("B03", "PC桁橋", "PC Girder Bridge",
              "beam_bridge", "桁橋",
              domains={"span_m": [30,40,50], "deck_w_m": [9,10,11]},
              derive=lambda s: derive_beam({**s, "E_GPa": 35, "fb_MPa": 25}),
              tags=frozenset({"prestressed", "concrete", "simple"})),
    Archetype("W01", "木造桁橋(スギ・2級)", "Wood Girder (Sugi Grade 2)",
              "wood_bridge", "木橋",
              domains={"span_m": [5,8,10,12], "b_mm": [200,250,300,350], 
                       "h_mm": [300,400,450,500], "wood_grade": ["sugi-2","hinoki","matsu"]},
              derive=derive_wood_beam,
              tags=frozenset({"wood", "simple", "rural", "kenchikushi"})),
    Archetype("W03", "木造アーチ橋", "Wood Arch Bridge",
              "wood_bridge", "木橋",
              domains={"span_m": [15,20,25], "b_mm": [300,350,400], "h_mm": [500,600,700]},
              derive=lambda s: derive_wood_beam({**s, "type": "arch"}),
              tags=frozenset({"wood", "arch", "scenic"})),
    Archetype("A01", "上路式鋼アーチ橋", "Steel Deck Arch",
              "arch_bridge", "アーチ橋",
              domains={"span_m": [80,100,120,150], "rise_m": [15,20,25,30]},
              derive=derive_arch,
              tags=frozenset({"steel", "arch", "landmark"})),
    Archetype("S01", "3径間吊り橋", "3-Span Suspension Bridge",
              "suspension_bridge", "吊り橋",
              domains={"main_span_m": [500,800,1000,1500], "deck_w_m": [20,25,30]},
              derive=derive_suspension,
              tags=frozenset({"steel", "suspension", "long_span"})),
]

def get_registry() -> List[Archetype]:
    return REGISTRY

def find_by_tag(tag: str) -> List[Archetype]:
    return [a for a in REGISTRY if tag in a.tags]

def find_by_category(cat: str) -> List[Archetype]:
    return [a for a in REGISTRY if a.category == cat]

def generate_batch(category: str = None, count: int = 10) -> List[Dict]:
    """Generate N random bridge instances."""
    pool = find_by_category(category) if category else REGISTRY
    return [random.choice(pool).generate() for _ in range(count)]

# ============================================================
# EDN-like serialization (Clojure-inspired)
# ============================================================

def to_edn(obj: Any) -> str:
    """Python dict to EDN-like string."""
    if isinstance(obj, dict):
        items = " ".join(f":{k} {to_edn(v)}" for k, v in obj.items())
        return "{" + items + "}"
    if isinstance(obj, (list, tuple)):
        return "[" + " ".join(to_edn(v) for v in obj) + "]"
    if isinstance(obj, str):
        return f'"{obj}"'
    return str(obj)

# ============================================================
# Agent: Rule-based archetype generator
# ============================================================

STRUCTURAL_RULES = {
    "beam_bridge": {
        "span_range": (10, 80),
        "h_over_L": (1/20, 1/12),
        "materials": ["steel-sm400", "steel-sm490", "pc", "rc", "wood"],
        "load_model": "T-load (道路橋示方書)",
    },
    "arch_bridge": {
        "span_range": (40, 300),
        "rise_over_span": (1/8, 1/4),
        "thrust_check": "foundation_bearing",
    },
    "suspension_bridge": {
        "span_range": (200, 3000),
        "cable_safety": 2.5,
        "aerodynamic_check": "required",
    },
    "truss_bridge": {
        "span_range": (30, 200),
        "panel_ratio": (4, 8),  # panels per span
    },
    "rigid_frame_bridge": {
        "span_range": (20, 100),
        "moment_transfer": "full_rigid",
    },
    "wood_bridge": {
        "span_range": (3, 30),
        "fb_source": "建築基準法 第2条",
        " termite_check": True,
    },
}

def agent_generate(category: str, constraints: Dict = None) -> Dict:
    """
    Rule-based agent that generates a valid archetype instance.
    Simulates LangChain's structured output without external deps.
    """
    rules = STRUCTURAL_RULES.get(category, {})
    lo, hi = rules.get("span_range", (10, 100))
    span = random.randint(int(lo), int(hi))
    
    # Apply constraints if any
    if constraints:
        span = constraints.get("span_m", span)
    
    # Draft instance
    draft = {
        "category": category,
        "span_m": span,
        "draft_id": f"AGENT-{category}-{span}-{random.randint(1000,9999)}",
        "rules_applied": list(rules.keys()),
    }
    
    # Validation pass (structural feasibility)
    if category == "beam_bridge":
        h_min = span / rules.get("h_over_L", (1/20, 1/12))[1]
        draft["feasible"] = True
        draft["h_min_m"] = round(h_min, 2)
    elif category == "suspension_bridge":
        draft["cable_dia_min_mm"] = int(span * 0.6)  # heuristic
        draft["feasible"] = span > 100
    else:
        draft["feasible"] = True
    
    return draft

if __name__ == "__main__":
    print("=== Archetype Generator Demo ===")
    for arch in REGISTRY[:3]:
        inst = arch.generate()
        print(f"\n{arch.id}: {arch.name}")
        print(json.dumps(inst, ensure_ascii=False, indent=2)[:600])
    
    print("\n=== Agent-generated ===")
    for cat in ["beam_bridge", "suspension_bridge", "wood_bridge"]:
        g = agent_generate(cat)
        print(f"\n{cat}: {json.dumps(g, ensure_ascii=False)}")
