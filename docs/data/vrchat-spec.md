# VRChat向け構造力学素材 — 出力仕様

## 1. 基本フォーマット

| 用途 | 形式 | 备注 |
|------|------|------|
| 3Dモデル | `.fbx` (Ascii 6.1) | Blender→Unity経由で最安定 |
| アニメーション | `.anim` + AnimatorController | たわみ・破壊シーケンス |
| マテリアル | Unity `.mat` (Standard/URP) | 応力ヒートマップ用 shader |
| テクスチャ | `.png` (1024~2048, sRGB) | カラーバンド、破断面 |
| 軽量化モデル | `.obj` + `.mtl` | Quest対応用ローポリ |
| ワールドギミック | UdonSharp `.cs` | インタラクション用 |
| アバター装着 | ボーン付き `.fbx` + VRC Avatar Descriptor | 教育用アバター |
| 動画像 | `.mp4` (H.264, 1080p60) | ロード画面・説明用 |
| VRM | `.vrm` (VRM 0.x/1.0) | 他プラットフォーム互換 |

## 2. 構造力学特有アセット

### A. 応力可視化マテリアル (Shader)
- HLSLシェーダー: 頂点カラーで応力分布をリアルタイム描画
- 入力: `float _StressRatio` (0~1+) → 青→黄→赤のグラデーション
- UV展開不要: 頂点カラーまたはプロシージャル

### B. 破壊シーケンスアニメーション
- FBXに複数アニメーションクリップを埋め込み:
  - `idle` (静止)
  - `deflect_loop` (たわみ振動)
  - `crack_emerge` (亀裂発生)
  - `fracture` (破断・分離)
- Shapes/Blendshapeでひずみ表現

### C. インタラクティブ部材 (UdonSharp)
```csharp
// ユーザーが触れると応力度が変化
public float userLoad = 0f; // 手のコライダー接触で増加
public float maxStress = 1.0f; // 破断閾値
public void OnPlayerTriggerStay(VRCPlayerApi player) { ... }
```

### D. 床板・壁のサンプルセット
- ラーメン架構: 柱+梁の接合部モジュール (16種)
- 耐力壁: 開口部比率を変えた壁パネル (4種)
- ブレース: X型/V型/片持型 (3種)
- 支承: ラバー支承/ピン支承/固定支承 (3種)

## 3. Bridge-Archetypes-100 → VRChat 変換パイプライン

```
docs/data/bridge-data.json
  ↓ Python変換スクリプト
assets/vrchat/prefabs/          # Unity Prefab出力
assets/vrchat/materials/        # 応力gradient mat
assets/vrchat/animations/       # FBX clip
assets/vrchat/textures/         # 亀裂・破断面 texture
assets/vrchat/udon/             # U# スクリプト
```

### JSON → Unity変換に必要な derived data
- `bridge-vrchat.json`: 各構造の представитель的寸法 (VRスケール 1:1 → 1unit=1m)
- `bridge-materials.json`: Unity Standard Shader のパラメータ対応表
  - youngs_modulus → stiffness係数 (アニメーション速度に反映)
  - fb → stress color閾値
- `bridge-animations.json`: アニメーション キーフレーム定義
  - たわみ曲線: P(t) → δ(t)
  - 色変化: σ(t)/fb → gradient UV offset

## 4. VRChatワールド展示用構成案

### 展示フロア構成
| ゾーン | 内容 | アセット数 |
|--------|------|-----------|
| 入門ゾーン | 単純梁のS図/M図立体化 | 3 |
| 材料ゾーン | 木材/鋼材/RCの断面サンプル（等比スケール） | 6 |
| 破壊ゾーン | 座屈→破断のスローモーション展示 | 5 |
| 橋ゾーン | 吊り橋・トラス橋の歩行可能ワイヤーフレーム | 2 |
| 試験ゾーン | M図描画クイズ（Udonで採点） | 1 |

## 5. ファイル命名規則

```
ba_{category}_{id}_{variant}.{ext}

例:
ba_beam_B01_simple_deflect.fbx        # 単純梁 たわみアニメ付き
ba_beam_B01_simple_stress.mat          # 応力gradientマテリアル
ba_arch_A01_deck_arch.prefab           # アーチ橋 prefab (Udon付き)
ba_material_steel_SM400.tga           # 鋼材表面 texture
ba_failure_buckle_anim.anim            # 座屈アニメーション
```

## 6. Quest対応チェックリスト

- [ ] ポリゴン数: 部材単体 < 5,000 tris
- [ ] テクスチャ: 1枚にアトラス化、最大 1024x1024
- [ ] マテリアル: Standardのみ、Custom Shader → Simple Lit フォールバック
- [ ] ボーン: アニメーションは Transform アニメ (Skinned Mesh避ける)
- [ ] ライト: Realtime Light 削除、Baked/Reflection Probeのみ
