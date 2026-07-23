const BRIDGE_DATA = {
  "schema_version": "1.0",
  "note": "橋の構造100選 - Mechanical parameters for FEM analysis",
  "categories": {
    "beam_bridge": {
      "ja": "桁橋",
      "structures": [
        {
          "id": "B01",
          "name": "単純合成I桁橋",
          "span_m": 30,
          "deck_w_m": 9,
          "h_m": 2.5,
          "E_GPa": 200,
          "A_cm2": 800,
          "I_m4": 0.35,
          "fb_MPa": 210,
          "material": "鋼(SM400)",
          "type": "simple"
        },
        {
          "id": "B02",
          "name": "連続箱桁橋",
          "span_m": 60,
          "deck_w_m": 12,
          "h_m": 3.2,
          "E_GPa": 200,
          "A_cm2": 1200,
          "I_m4": 1.8,
          "fb_MPa": 210,
          "material": "鋼(SM490)",
          "type": "continuous"
        },
        {
          "id": "B03",
          "name": "PC桁橋",
          "span_m": 40,
          "deck_w_m": 10,
          "h_m": 2.2,
          "E_GPa": 35,
          "A_cm2": 1500,
          "I_m4": 0.9,
          "fb_MPa": 25,
          "material": "PC",
          "type": "simple"
        },
        {
          "id": "B04",
          "name": "単純T桁橋",
          "span_m": 20,
          "deck_w_m": 8,
          "h_m": 1.8,
          "E_GPa": 30,
          "A_cm2": 600,
          "I_m4": 0.15,
          "fb_MPa": 18,
          "material": "RC",
          "type": "simple"
        },
        {
          "id": "B05",
          "name": "合成桁橋(横おろし版)",
          "span_m": 35,
          "deck_w_m": 9.5,
          "h_m": 2.0,
          "E_GPa": 200,
          "A_cm2": 900,
          "I_m4": 0.5,
          "fb_MPa": 210,
          "material": "鋼",
          "type": "simple"
        }
      ]
    },
    "arch_bridge": {
      "ja": "アーチ橋",
      "structures": [
        {
          "id": "A01",
          "name": "上路式鋼アーチ橋",
          "span_m": 120,
          "rise_m": 24,
          "deck_w_m": 10,
          "E_GPa": 200,
          "A_arch_cm2": 3000,
          "I_m4": 8.0,
          "fb_MPa": 210,
          "material": "鋼",
          "type": "deck_arch"
        },
        {
          "id": "A02",
          "name": "下路式RCアーチ橋",
          "span_m": 80,
          "rise_m": 16,
          "deck_w_m": 8,
          "E_GPa": 30,
          "A_arch_cm2": 2500,
          "I_m4": 3.5,
          "fb_MPa": 24,
          "material": "RC",
          "type": "through_arch"
        },
        {
          "id": "A03",
          "name": "中承式鋼アーチ橋",
          "span_m": 200,
          "rise_m": 40,
          "deck_w_m": 12,
          "E_GPa": 200,
          "A_arch_cm2": 5000,
          "I_m4": 25.0,
          "fb_MPa": 325,
          "material": "鋼(SM520)",
          "type": "half_through"
        }
      ]
    },
    "suspension_bridge": {
      "ja": "吊り橋",
      "structures": [
        {
          "id": "S01",
          "name": "3径間吊り橋",
          "main_span_m": 1000,
          "side_span_m": 400,
          "tower_h_m": 200,
          "deck_w_m": 25,
          "cable_dia_mm": 700,
          "E_GPa": 200,
          "fb_MPa": 1200,
          "material": "鋼(PWS)",
          "type": "3span"
        },
        {
          "id": "S02",
          "name": "2径間吊り橋",
          "main_span_m": 600,
          "tower_h_m": 120,
          "deck_w_m": 18,
          "cable_dia_mm": 500,
          "E_GPa": 200,
          "fb_MPa": 1200,
          "material": "鋼",
          "type": "2span"
        },
        {
          "id": "S03",
          "name": "斜張橋(ハープ型)",
          "span_m": 400,
          "tower_h_m": 150,
          "deck_w_m": 20,
          "E_GPa": 200,
          "cable_count": 80,
          "fb_MPa": 1200,
          "material": "鋼",
          "type": "cable_stayed_harp"
        }
      ]
    },
    "truss_bridge": {
      "ja": "トラス橋",
      "structures": [
        {
          "id": "T01",
          "name": "ワーレントラス橋",
          "span_m": 50,
          "depth_m": 8,
          "deck_w_m": 8,
          "E_GPa": 200,
          "A_cm2": 5000,
          "fb_MPa": 210,
          "material": "鋼(SM400)",
          "type": "warren"
        },
        {
          "id": "T02",
          "name": "プラットトラス橋",
          "span_m": 40,
          "depth_m": 7,
          "deck_w_m": 7,
          "E_GPa": 200,
          "A_cm2": 4500,
          "fb_MPa": 210,
          "material": "鋼",
          "type": "pratt"
        }
      ]
    },
    "rigid_frame_bridge": {
      "ja": "ラーメン橋",
      "structures": [
        {
          "id": "R01",
          "name": "鋼ラーメン橋",
          "span_m": 50,
          "h_pier_m": 15,
          "deck_w_m": 9,
          "E_GPa": 200,
          "A_cm2": 6000,
          "I_m4": 2.0,
          "fb_MPa": 210,
          "material": "鋼",
          "type": "steel_rigid"
        },
        {
          "id": "R02",
          "name": "RCラーメン橋",
          "span_m": 30,
          "h_pier_m": 10,
          "deck_w_m": 8,
          "E_GPa": 30,
          "A_cm2": 3000,
          "I_m4": 0.5,
          "fb_MPa": 24,
          "material": "RC",
          "type": "rc_rigid"
        }
      ]
    },
    "wood_bridge": {
      "ja": "木橋",
      "structures": [
        {
          "id": "W01",
          "name": "木造桁橋(スギ・2級)",
          "span_m": 10,
          "b_mm": 300,
          "h_mm": 450,
          "E_GPa": 10,
          "fb_MPa": 12,
          "material": "スギ",
          "type": "simple"
        },
        {
          "id": "W02",
          "name": "木造トラス橋",
          "span_m": 15,
          "b_mm": 250,
          "h_mm": 500,
          "E_GPa": 12,
          "fb_MPa": 14,
          "material": "ヒノキ",
          "type": "truss"
        },
        {
          "id": "W03",
          "name": "木造アーチ橋",
          "span_m": 20,
          "b_mm": 350,
          "h_mm": 600,
          "E_GPa": 11,
          "fb_MPa": 13,
          "material": "マツ",
          "type": "arch"
        }
      ]
    },
    "others": {
      "ja": "特殊構造",
      "structures": [
        {
          "id": "O01",
          "name": "可動橋(跳開橋)",
          "span_m": 30,
          "E_GPa": 200,
          "fb_MPa": 210,
          "material": "鋼",
          "type": "bascule"
        },
        {
          "id": "O02",
          "name": "可動橋(旋回橋)",
          "span_m": 40,
          "E_GPa": 200,
          "fb_MPa": 210,
          "material": "鋼",
          "type": "swing"
        },
        {
          "id": "O03",
          "name": "可動橋(昇開橋)",
          "span_m": 25,
          "E_GPa": 200,
          "fb_MPa": 210,
          "material": "鋼",
          "type": "lift"
        }
      ]
    }
  },
  "metadata": {
    "count_by_category": {
      "beam_bridge": 5,
      "arch_bridge": 3,
      "suspension_bridge": 3,
      "truss_bridge": 2,
      "rigid_frame_bridge": 2,
      "wood_bridge": 3,
      "others": 3
    },
    "total_structures": 21,
    "planned_extensions": [
      "cable_stayed_variants",
      "composite_girders",
      "long_span_tech",
      "historical_bridges",
      "international_examples"
    ]
  }
};
