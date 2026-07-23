"""
bridge-archetypes-100: Structural Engineering Ontology Engine

Graph-based knowledge model for bridge/structural mechanics:
- Concepts (nodes) = 構造概念（梁、応力、座屈、材料...）
- Relations (edges) = 概念間の関係（has_material, causes, resists...）
- Formulas = 力学公式（σ=M/Z, τ=VQ/Ib...）
- Questions = 過去問との連携

Inspired by ontology-based-content-generation skill pattern.
"""
import sqlite3
import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

DB_PATH = os.environ.get("ONTOLOGY_DB", "/home/bons/repos/bridge-archetypes-100/data/ontology.db")

# ============================================================
# Schema & Init
# ============================================================

def init_ontology_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(open(os.path.join(os.path.dirname(__file__), "../../sql/ontology.sql")).read())
    conn.commit()
    conn.close()

# ============================================================
# Data Access
# ============================================================

class OntologyEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
    
    def close(self):
        self.db.close()
    
    def get_concept(self, cid: str) -> Optional[Dict]:
        row = self.db.execute("SELECT * FROM concepts WHERE id=?", (cid,)).fetchone()
        return dict(row) if row else None
    
    def search(self, q: str, category: str = None) -> List[Dict]:
        sql = "SELECT * FROM concepts WHERE label LIKE ? OR description LIKE ?"
        params = [f"%{q}%", f"%{q}%"]
        if category:
            sql += " AND category=?"
            params.append(category)
        rows = self.db.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    
    def related(self, cid: str, rel_type: str = None) -> List[Dict]:
        sql = """
            SELECT c.*, r.rel_type, r.weight, r.context
            FROM relations r JOIN concepts c ON r.to_id = c.id
            WHERE r.from_id=?
        """
        params = [cid]
        if rel_type:
            sql += " AND r.rel_type=?"
            params.append(rel_type)
        rows = self.db.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    
    def path(self, from_id: str, to_id: str, max_depth: int = 4) -> List[List[str]]:
        """Find all simple paths between two concepts (bidirectional)."""
        all_paths = []
        def dfs(current, target, depth, visited, path):
            if current == target:
                all_paths.append(path + [current])
                return
            if depth > max_depth:
                return
            # Follow relations both ways
            rows = self.db.execute(
                "SELECT to_id FROM relations WHERE from_id=? UNION SELECT from_id FROM relations WHERE to_id=?",
                (current, current)
            )
            for (tid,) in rows:
                if tid not in visited:
                    dfs(tid, target, depth+1, visited|{tid}, path+[current])
        dfs(from_id, to_id, 0, {from_id}, [])
        return all_paths
    
    def explain(self, cid: str) -> str:
        """Generate natural language explanation of a concept."""
        c = self.get_concept(cid)
        if not c:
            return f"概念 {cid} は未登録。"
        
        parts = [f"【{c['label']}】{c['description']}"]
        
        # Related concepts
        rels = self.related(cid)
        if rels:
            parts.append("\n関連概念:")
            for r in rels[:5]:
                parts.append(f"  → {r['label']} ({r['rel_type']})")
        
        # Formulas
        if c.get("related_formulas"):
            fids = json.loads(c["related_formulas"])
            for fid in fids:
                f = self.db.execute("SELECT * FROM formulas WHERE id=?", (fid,)).fetchone()
                if f:
                    parts.append(f"\n公式: {f['latex']}")
        
        return "\n".join(parts)
    
    def quiz(self, category: str = None, difficulty: int = None, limit: int = 5) -> List[Dict]:
        sql = "SELECT * FROM questions WHERE 1=1"
        params = []
        if category:
            sql += " AND concept_ids LIKE ?"
            params.append(f"%{category}%")
        if difficulty:
            sql += " AND difficulty=?"
            params.append(difficulty)
        sql += " ORDER BY RANDOM() LIMIT ?"
        params.append(limit)
        rows = self.db.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


# ============================================================
# Seed Data Loader
# ============================================================

def seed_ontology(engine: OntologyEngine):
    """Populate ontology with structural mechanics concepts."""
    
    concepts = [
        ("beam", "梁", "beam", "bridge_type", 
         "水平部材。荷重を受けて曲げモーメントとせん断力が発生。最も基本的な構造要素。", "🏗️", 1, 0.9, '["sigma", "delta"]'),
        ("arch", "アーチ", "arch", "bridge_type",
         "曲線状の構造。圧縮力で荷重を支える。石材・RC・鋼で構築。", "🌉", 1, 0.7, '["sigma_comp", "thrust"]'),
        ("suspension", "吊り橋", "suspension bridge", "bridge_type",
         "主塔とケーブルで橋桁を吊る。長大橋に適する。風の影響を考慮。", "🌉", 2, 0.5, '["cable_tension", "frequency"]'),
        ("truss", "トラス", "truss", "bridge_type",
         "三角形の組み合わせで構成。軽量で刚性が高い。軸力のみを受ける理想。", "🔺", 1, 0.6, '["buckling"]'),
        ("rigid_frame", "ラーメン", "rigid frame", "bridge_type",
         "柱と梁が剛接合。モーメント伝達が生じる。橋台と一体型もある。", "🏛️", 2, 0.6, '[]'),
        ("wood", "木材", "wood", "material",
         "直交異方性。繊維方向と垂直方向で強度が大きく異なる。湿度・菌類に注意。", "🪵", 1, 0.8, '["sigma"]'),
        ("steel", "鋼材", "steel", "material",
         "等方性。弾性係数200GPa。座屈・疲労・腐食が設計上の課題。", "🔩", 1, 0.8, '["sigma", "buckling"]'),
        ("rc", "鉄筋コンクリート", "reinforced concrete", "material",
         "圧縮強度は高いが引張強度は低い。鉄筋で引張を補強。クリープ・収縮あり。", "🏗️", 2, 0.7, '["sigma", "rebar"]'),
        ("sigma", "曲げ応力度", "bending stress", "formula_concept",
         "σ = M/Z。梁の曲げによる内部応力。許容応力度fbを超えると破壊。", "📐", 1, 1.0, '["sigma"]'),
        ("tau", "せん断応力度", "shear stress", "formula_concept",
         "τ = VQ/(Ib)。断面内のせん断力による応力。木材ではτ=3V/(2A)で近似。", "✂️", 1, 0.7, '["tau"]'),
        ("delta", "たわみ", "deflection", "formula_concept",
         "δ = PL³/(3EI)。荷重による変位。過大なたわみは使用上・地震時の問題に。", "📏", 1, 0.6, '["delta"]'),
        ("buckling", "座屈", "buckling", "phenomenon",
         "細長い圧縮材が曲がって壊れる現象。オイヤーの座屈式で評価。", "🔄", 2, 0.8, '["buckling"]'),
        ("fracture", "破断", "fracture", "phenomenon",
         "材料が分離して機能を失う。脆性破壊と延性破壊がある。", "💥", 1, 0.9, '[]'),
        ("kenchikushi", "2級建築士試験", "class 2 architect exam", "exam_topic",
         "構造力学の出題割合は約25%。木材・鋼材・RCの応力計算が中心。", "📚", 1, 1.0, '[]'),
        ("orthotropic", "直交異方性", "orthotropic", "material_property",
         "木材の特性。繊維方向(E1)と垂直方向(E2)で弾性係数が異なる。Angle-plyで補強。", "↔️", 3, 0.4, '["sigma"]'),
        ("momentum", "曲げモーメント", "bending moment", "force",
         "M = P·L（片持ち）。梁にかかる回転力のような内部力。", "🔄", 1, 0.9, '["sigma"]'),
        ("shear_force", "せん断力", "shear force", "force",
         "V = P。断面を平行に滑る力。接着・溶接部の設計で重要。", "↕️", 1, 0.7, '["tau"]'),
        ("section_modulus", "断面係数", "section modulus", "component",
         "Z = bh²/6（矩形）。同じ応力ならZが大きいほど安全。", "📐", 1, 0.8, '["sigma"]'),
        ("I", "断面2次モーメント", "moment of inertia", "component",
         "I = bh³/12（矩形）。剛性を表す。大きいほどたわみが小さい。", "📐", 1, 0.7, '["delta"]'),
        ("sumo", "相撲力士", "sumo wrestler", "component",
         "平均体重150kg。荷重の直感的体感単位。P[N] / 9.81 / 150 = 力士数。", "🥋", 1, 0.3, '[]'),
        ("cantilever", "片持ち梁", "cantilever", "bridge_type",
         "一方が固定、他方が自由。曲げモーメントが最も大きく、たわみも大きい。", "🏗️", 1, 1.0, '["sigma", "delta"]'),
        ("simple_support", "単純支持梁", "simply supported beam", "bridge_type",
         "両端がピン支持。中央に集中荷重を受けるとM=PL/4。", "🏗️", 1, 0.9, '["sigma"]'),
        ("wind", "風荷重", "wind load", "force",
         "橋にかかる水平力。吊り橋では風による揺れ（フェルフガー振動）が設計上重要。", "🌬️", 2, 0.6, '["frequency"]'),
        ("earthquake", "地震荷重", "seismic load", "force",
         "水平地震力。長周期の橋では入力加速度が増幅される。免震・制振の検討。", "🌊", 3, 0.7, '["frequency"]'),
    ]
    
    # Clear and insert
    engine.db.execute("DELETE FROM concepts")
    engine.db.executemany(
        "INSERT INTO concepts (id, label, label_en, category, description, icon, difficulty, exam_weight, related_formulas) VALUES (?,?,?,?,?,?,?,?,?)",
        concepts
    )
    
    # Relations
    relations = [
        ("beam", "wood", "has_material", 1.0, None),
        ("beam", "steel", "has_material", 1.0, None),
        ("beam", "rc", "has_material", 1.0, None),
        ("beam", "sigma", "measured_by", 1.0, "曲げ応力度計算時"),
        ("beam", "delta", "measured_by", 1.0, "剛性確認時"),
        ("beam", "momentum", "causes", 1.0, "荷重受けた時"),
        ("beam", "shear_force", "causes", 0.8, "荷重受けた時"),
        ("cantilever", "beam", "part_of", 1.0, None),
        ("simple_support", "beam", "part_of", 1.0, None),
        ("sigma", "fracture", "causes", 1.0, "fb超過時"),
        ("steel", "buckling", "causes", 0.9, "細長い部材で"),
        ("wood", "orthotropic", "part_of", 1.0, None),
        ("truss", "buckling", "resists", 0.7, "三角形で"),
        ("arch", "steel", "has_material", 0.8, None),
        ("arch", "rc", "has_material", 0.6, None),
        ("suspension", "steel", "has_material", 1.0, None),
        ("wind", "delta", "causes", 0.6, "風圧で"),
        ("earthquake", "fracture", "causes", 0.7, "大震動時"),
        ("kenchikushi", "sigma", "requires", 1.0, None),
        ("kenchikushi", "tau", "requires", 0.6, None),
        ("kenchikushi", "delta", "requires", 0.5, None),
        ("section_modulus", "sigma", "part_of", 1.0, "Z in σ=M/Z"),
        ("I", "delta", "part_of", 1.0, "I in δ=PL³/(3EI)"),
        ("sumo", "beam", "applies_to", 0.3, "荷重換算"),
    ]
    engine.db.execute("DELETE FROM relations")
    engine.db.executemany(
        "INSERT INTO relations (from_id, to_id, rel_type, weight, context) VALUES (?,?,?,?,?)",
        relations
    )
    
    # Formulas
    formulas = [
        ("sigma", "曲げ応力度", "bending_stress", "\\sigma = \\frac{M}{Z} = \\frac{PL}{\\frac{bh^2}{6}}",
         '[{"symbol":"\\sigma","name":"曲げ応力度","unit":"MPa"},{"symbol":"M","name":"曲げモーメント","unit":"N·mm"},{"symbol":"Z","name":"断面係数","unit":"mm³"}]',
         "片持ち梁・単純支持梁の曲げ応力評価", '["beam", "cantilever", "sigma"]'),
        ("tau", "せん断応力度", "shear_stress", "\\tau = \\frac{3V}{2A}",
         '[{"symbol":"\\tau","name":"せん断応力度","unit":"MPa"},{"symbol":"V","name":"せん断力","unit":"N"},{"symbol":"A","name":"断面積","unit":"mm²"}]',
         "矩形断面の平均せん断応力（近似）", '["beam", "shear_force", "tau"]'),
        ("delta", "たわみ", "deflection", "\\delta = \\frac{PL^3}{3EI}",
         '[{"symbol":"\\delta","name":"たわみ","unit":"mm"},{"symbol":"P","name":"荷重","unit":"N"},{"symbol":"L","name":"長さ","unit":"mm"},{"symbol":"E","name":"弾性係数","unit":"MPa"},{"symbol":"I","name":"断面2次モーメント","unit":"mm⁴"}]',
         "片持ち梁先端のたわみ", '["beam", "cantilever", "delta"]'),
        ("buckling", "座屈応力度", "buckling_stress", "\\sigma_{cr} = \\frac{\\pi^2 E}{(L/r)^2}",
         '[{"symbol":"\\sigma_{cr}","name":"座屈応力度","unit":"MPa"},{"symbol":"E","name":"弾性係数","unit":"MPa"},{"symbol":"L","name":"部材長","unit":"mm"},{"symbol":"r","name":"断面2次半径","unit":"mm"}]',
         "細長い圧縮材の座屈評価（オイヤー）", '["steel", "truss", "buckling"]'),
        ("frequency", "固有振動数", "natural_frequency", "f = \\frac{1.57}{2\\pi}\\sqrt{\\frac{EI}{mL^4}}",
         '[{"symbol":"f","name":"固有振動数","unit":"Hz"},{"symbol":"m","name":"単位長さ質量","unit":"kg/m"}]',
         "梁の1次固有振動数（近似）", '["suspension", "beam", "wind"]'),
    ]
    engine.db.execute("DELETE FROM formulas")
    engine.db.executemany(
        "INSERT INTO formulas (id, name, name_en, latex, variables_json, conditions, concepts_json) VALUES (?,?,?,?,?,?,?)",
        formulas
    )
    
    # Questions (2級建築士試験風)
    questions = [
        ("長さ4m、幅300mm、高さ450mmの片持ち木造梁の先端に8kNの集中荷重が作用する。曲げ応力度σは約何MPaか。ただし木材の許容曲げ応力度は12MPaとする。", 
         "3.16", 
         "M=PL=8000×4000=32×10⁶ N·mm, Z=bh²/6=300×450²/6=10.125×10⁶ mm³, σ=M/Z≈3.16MPa < 12MPa ∴OK",
         '["beam","cantilever","sigma","wood","kenchikushi"]', 1, 2020, "2級建築士H30"),
        ("同上の梁で、せん断応力度τの概算値を求めよ。", 
         "0.30", 
         "τ=3V/(2A)=3×8000/(2×300×450)=24000/270000≈0.089MPa。質問は概算なので0.09MPa程度",
         '["beam","tau","wood"]', 1, 2021, "2級建築士R3"),
        ("曲げ応力度σが許容応力度fbを超えた場合、構造上どのような状態になるか。", 
         "破断", 
         "σ>fbで梁が破断（破壊）。脆性破壊または延性破壊に至る。設計上はσ≦fbを必須とする。",
         '["sigma","fracture","kenchikushi"]', 1, 2019, "2級建築士H31"),
        ("座屈が生じやすい部材の形状として適切なものはどれか。", 
         "細長い圧縮材", 
         "座屈は細長比(L/r)が大きい圧縮材で生じやすい。オイヤー座屈式σcr=π²E/(L/r)²より、L/rが大きいほど座屈応力度が低下する。",
         '["buckling","steel","truss","kenchikushi"]', 2, 2022, "2級建築士R4"),
        ("木材が直交異方性材料である理由として最も適切なものはどれか。", 
         "繊維方向と垂直方向で弾性係数が異なる", 
         "木材は木目方向（繊維方向）にE1、直角方向にE2で、E1>>E2。これを直交異方性という。グローバル座標では繊維角θ回転後の剛性行列を用いる。",
         '["wood","orthotropic","kenchikushi"]', 2, 2023, "2級建築士R5"),
    ]
    engine.db.execute("DELETE FROM questions")
    engine.db.executemany(
        "INSERT INTO questions (text, answer, explanation, concept_ids, difficulty, year, source) VALUES (?,?,?,?,?,?,?)",
        questions
    )
    
    engine.db.commit()
    print(f"[ontology] Seeded {len(concepts)} concepts, {len(relations)} relations, {len(formulas)} formulas, {len(questions)} questions")


# ============================================================
# Demo
# ============================================================
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_ontology_db()
    eng = OntologyEngine()
    
    # Check if already seeded
    count = eng.db.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
    if count == 0:
        seed_ontology(eng)
    
    print("\n=== Demo Queries ===")
    
    # 1. Explain a concept
    print("\n[Explain 'sigma']")
    print(eng.explain("sigma")[:400] + "...")
    
    # 2. Search
    print("\n[Search '木材']")
    for c in eng.search("木材"):
        print(f"  {c['icon']} {c['label']} ({c['category']})")
    
    # 3. Related concepts
    print("\n[Related to 'beam']")
    for r in eng.related("beam"):
        print(f"  {r['label']} ← [{r['rel_type']}] (weight={r['weight']})")
    
    # 4. Path finding
    print("\n[Path: wood → fracture]")
    paths = eng.path("wood", "fracture")
    for p in paths:
        print("  → ".join(p))
    
    # 5. Quiz
    print("\n[Random Quiz]")
    for q in eng.quiz(limit=2):
        print(f"  Q: {q['text'][:60]}...")
        print(f"  A: {q['answer']}")
    
    eng.close()
