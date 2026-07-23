# bridge-archetypes-100（橋の構造100選）

## Overview
交互式橋梁構造学習＋FEM可視化システム。建筑士試験（2級構造）対応。

## Architecture

```
bridge-archetypes-100/
├── backend/src/
│   ├── main.py          # FastAPI unified server
│   ├── archetypes.py    # Functional archetype generator
│   ├── db.py            # SQLite persistence
│   └── main.py          # Wood beam FEM solver
├── frontend/static/
│   ├── index.html       # Canvas UI
│   └── app.js           # Real-time stress viz
├── haskell/src/
│   └── Core.hs          # Pure functional orthotropic solver
├── scripts/
│   └── auto_record.py   # Playwright → MP4 pipeline
├── sql/
│   └── schema.sql       # DB schema
├── data/
│   └── archetypes.json  # Seed data
└── flake.nix            # Nix reproducible devShell

```

## Quick Start

```bash
# 1. Nix dev shell
nix develop

# 2. Local Python
pip install fastapi uvicorn numpy

# 3. Start server
cd /home/bons/repos/bridge-archetypes-100
./start.sh dev

# 4. Open browser
http://localhost:8000/static/index.html

# 5. Auto-record MP4
./start.sh record
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | App status |
| `/solve` | POST | Run FEM simulation |
| `/archetypes` | GET | List mother archetypes |
| `/archetypes/{id}` | GET | Generate instance |
| `/generate` | POST | Agent generates new archetype |
| `/sims` | GET | Simulation history |

## Sumo Rider Physics

Load `P [N]` → Sumo wrestlers (�都是由 average 150kg):
- `sumo_count = P / 9.81 / 150`
- "7 sumos" = 7×150 = 1050kg ≈ 10.3kN

## Tests

```bash
cd backend/src
python3 archetypes.py    # generator demo
python3 -c "from main import solve_py; ..."  # solver test
```

## License
MIT
