"""
bridge-archetypes-100: LangChain Structural Engineer Agent

Pure Python implementation (no external LLM deps required by default).
Simulates LangChain tool-use pattern with rule-based reasoning + optional LLM.
"""
import json
import math
import os
import re
from typing import Dict, List, Any, Optional

# ============================================================
# Tools (ReAct pattern simulated)
# ============================================================

def tool_beam_stress(params: Dict) -> Dict:
    """Calculate beam bending stress."""
    L = params.get("L_mm", 4000)
    b = params.get("b_mm", 300)
    h = params.get("h_mm", 450)
    E = params.get("E_MPa", 10000)
    fb = params.get("fb_MPa", 12)
    P = params.get("P_N", 10000)
    support = params.get("support", "cantilever")
    I = b * h**3 / 12
    Z = b * h**2 / 6
    M = P * L if support == "cantilever" else P * L / 4
    sigma = M / Z
    delta = P * L**3 / (3 * E * I)
    return {
        "sigma_max_MPa": round(sigma, 2),
        "delta_mm": round(delta, 3),
        "fractured": sigma > fb,
        "sigma_ratio": round(sigma / fb, 3),
        "required_h_mm": round(math.sqrt(6 * M / (fb * b)), 1) if sigma > fb else h,
    }

def tool_generate_archetype(params: Dict) -> Dict:
    """Generate a bridge archetype from category + constraints."""
    category = params.get("category", "beam_bridge")
    span = params.get("span_m", 30)
    from archetypes import agent_generate
    return agent_generate(category, {"span_m": span})

def tool_explain_formula(params: Dict) -> str:
    """Explain structural mechanics formula in Japanese."""
    formula = params.get("formula", "sigma")
    explanations = {
        "sigma": "曲げ応力度 σ = M/Z：梁にかかる曲げモーメントMを断面係数Zで割った値。単位はMPa。建築基準法で許容応力度fbを超えたらNG。",
        "tau": "せん断応力度 τ = V·Q/(I·b)：断面にかかるせん断力Vから計算。木材では平均値τ=3V/(2A)で近似。",
        "delta": "たわみ δ = PL³/(3EI)：荷重P・長さL・弾性係数E・断面2次モーメントIで決まる。大きすぎると振動や見た目の問題に。",
        "Z": "断面係数 Z = bh²/6：矩形断面の場合。梁の曲げ抵抗能力を表す。Zが大きいほど同じ応力を受けても安全。",
        "frequency": "固有周期 T = 2π√(m/k)：質量mと剛性kで決まる。人の歩行周波数(1.6-2.2Hz)と共振しないよう設計。",
        "buckling": "座屈 σcr = π²E/(L/r)²：細長い柱や圧縮材が曲がって壊れる現象。細長比L/rが大きいほど座屈しやすい。",
    }
    return explanations.get(formula, f"「{formula}」の説明は未登録。sigma/tau/delta/Z/frequency/bucklingに対応。")

def tool_sumo_convert(params: Dict) -> Dict:
    """Convert load to sumo wrestlers."""
    P = params.get("P_N", 0)
    count = P / 9.81 / 150
    return {
        "sumo_count": round(count, 1),
        "total_kg": round(count * 150, 0),
        "description": f"{round(count, 1)}人分の相撲力士（{round(count*150)}kg）に相当"
    }

# ============================================================
# Agent Core (ReAct pattern without LLM)
# ============================================================

class StructuralAgent:
    TOOLS = {
        "beam_stress": tool_beam_stress,
        "generate_archetype": tool_generate_archetype,
        "explain_formula": tool_explain_formula,
        "sumo_convert": tool_sumo_convert,
    }
    
    def _extract_params(self, q: str) -> Dict:
        """Extract numerical parameters from Japanese query."""
        nums = re.findall(r'(\d+(?:\.\d+)?)(?:\s*(mm|m|kN|N|MPa|GPa))?', q, re.I)
        params = {}
        for val, unit in nums:
            v = float(val)
            u = unit.lower() if unit else ""
            if "m" in u and "mm" not in u: params["L_mm"] = v * 1000
            elif "mm" in u:
                if "高" in q or "h" in q.lower(): params["h_mm"] = v
                elif "幅" in q or "b" in q.lower(): params["b_mm"] = v
                else: params.setdefault("L_mm", v)
            elif "gpa" in u: params["E_MPa"] = v * 1000
            elif "mpa" in u: params["fb_MPa"] = v
            elif "kn" in u: params["P_N"] = v * 1000
            elif "n" in u: params["P_N"] = v
            else:
                if not params.get("L_mm"): params["L_mm"] = v
        params.setdefault("L_mm", 4000)
        params.setdefault("b_mm", 300)
        params.setdefault("h_mm", 450)
        params.setdefault("E_MPa", 10000)
        params.setdefault("fb_MPa", 12)
        params.setdefault("P_N", 10000)
        if "片持" in q or "cantilever" in q.lower():
            params["support"] = "cantilever"
        elif "単純" in q or "simple" in q.lower():
            params["support"] = "simple"
        return params
    
    def _detect_formula(self, q: str) -> str:
        if "曲げ" in q or "sigma" in q.lower(): return "sigma"
        elif "せん断" in q or "tau" in q.lower(): return "tau"
        elif "たわみ" in q or "delta" in q.lower(): return "delta"
        elif "断面" in q or "section" in q.lower(): return "Z"
        elif "固有" in q or "period" in q.lower() or "周期" in q: return "frequency"
        elif "座屈" in q or "buckling" in q.lower(): return "buckling"
        return "sigma"
    
    def think(self, query: str) -> Dict:
        q = query.lower()
        thoughts = []
        actions = []
        
        # Intent priority: explanation > sumo > generate > beam calculation
        
        if any(w in q for w in ["とは", "なに", "意味", "説明", "what is", "explain", "公式"]):
            formula = self._detect_formula(query)
            thoughts.append(f"Explain formula: {formula}")
            actions.append({"tool": "explain_formula", "params": {"formula": formula}})
            result = tool_explain_formula({"formula": formula})
            return {
                "thoughts": thoughts, "actions": actions,
                "result": result,
                "natural_language": result,
            }
        
        if any(w in q for w in ["sumo", "力士", "何キロ", "何ton", "何人"]):
            nums = re.findall(r'(\d+(?:\.\d+)?)(?:\s*(kN|N))?', query, re.I)
            P = 10000
            for val, unit in nums:
                v = float(val)
                if "kn" in (unit or "").lower(): P = v * 1000
                else: P = v
            result = tool_sumo_convert({"P_N": P})
            return {
                "thoughts": ["Convert load to sumos."],
                "actions": [{"tool": "sumo_convert", "params": {"P_N": P}}],
                "result": result,
                "natural_language": result["description"],
            }
        
        if any(w in q for w in ["generate", "生成", "作って", "create", "新しい"]):
            cat = "beam_bridge"
            if "アーチ" in query: cat = "arch_bridge"
            elif "吊" in query: cat = "suspension_bridge"
            elif "トラス" in query: cat = "truss_bridge"
            elif "木" in query: cat = "wood_bridge"
            result = tool_generate_archetype({"category": cat})
            return {
                "thoughts": [f"Generate archetype: {cat}"],
                "actions": [{"tool": "generate_archetype", "params": {"category": cat}}],
                "result": result,
                "natural_language": f"新しい{cat}のアーキタイプ: {result.get('draft_id', 'N/A')}（スパン{result.get('span_m', '?')}m、{'設計可' if result.get('feasible') else '要修正'}）",
            }
        
        if any(w in q for w in ["曲げ", "sigma", "応力", "破断", "梁", "beam", "荷重", "計算"]):
            params = self._extract_params(query)
            thoughts.append("Beam stress calculation requested.")
            actions.append({"tool": "beam_stress", "params": params})
            result = tool_beam_stress(params)
            
            nl = f"{params['L_mm']/1000}mの{'片持ち' if params.get('support')=='cantilever' else '単純支持'}梁に{params['P_N']/1000}kNをかけると、"
            nl += f"曲げ応力度は{result['sigma_max_MPa']}MPa。"
            if result['fractured']:
                nl += f"許容応力度{params['fb_MPa']}MPa超えで💥破断。必要梁高は{result['required_h_mm']}mm以上。"
            else:
                nl += f"許容比{result['sigma_ratio']:.0%}で安全。"
            
            return {
                "thoughts": thoughts, "actions": actions,
                "result": result,
                "natural_language": nl,
                "suggested_experiment": "スライダーでPを増やして破断点を探す",
            }
        
        return {
            "thoughts": ["No intent match."],
            "actions": [],
            "result": None,
            "natural_language": "『梁の応力計算』『公式の意味』『相撲換算』『構造生成』に対応。例:『長さ4mの片持ち梁に10kNをかけたら？』",
        }
    
    def chat(self, history: List[Dict], new_query: str) -> Dict:
        return self.think(new_query)


# ============================================================
# LangChain-compatible wrapper (optional)
# ============================================================
try:
    from langchain.tools import StructuredTool
    lc_tools = [
        StructuredTool.from_function(func=tool_beam_stress, name="beam_stress",
            description="Calc beam stress. Args: L_mm, b_mm, h_mm, E_MPa, fb_MPa, P_N, support"),
        StructuredTool.from_function(func=tool_explain_formula, name="explain_formula",
            description="Explain formula. formula=sigma|tau|delta|Z|frequency|buckling"),
    ]
except ImportError:
    lc_tools = []


# ============================================================
# CLI demo
# ============================================================
if __name__ == "__main__":
    agent = StructuralAgent()
    for q in [
        "長さ4m 幅300mm 高さ450mm の片持ち梁に10kNの荷重をかけたら破断する？",
        "曲げ応力度σとは何？",
        "80000Nは相撲力士何人分？",
        "木造アーチ橋を生成して",
    ]:
        print(f"\n{'='*50}")
        print(f"Q: {q}")
        r = agent.think(q)
        print(f"思考: {r['thoughts']}")
        print(f"A: {r['natural_language']}")
