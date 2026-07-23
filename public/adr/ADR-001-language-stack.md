# ADR-001: Language & Runtime Stack

## Status
Accepted

## Context
Need a full-stack web app for `橋の構造100選` FEM visualization:
- Interactive beam simulation with real-time calculation
- HTTP API for stress distribution
- Playwright auto-pilot for video generation
- Nix reproducible dev shell
- Hermes/AgentShell compatible (`python`,`node`,`ffmpeg` available)

Options considered:
1. **Python (FastAPI + Canvas JS)** — infra already present, async I/O, numpy
2. **Haskell (Servant + GHCJS/Wasm)** — type safety, but: no numpy equivalent, GHCJS/Wasm heavy compile times, Playwright integration less documented
3. **Rust (Axum + Yew)** — fast, but compile times, complex orthotropic FEM math would need reimplementation
4. **Pure TypeScript (Deno/Node + Canvas)** — no scientific computing libs for FEM matrix ops

## Decision
Use **Python (FastAPI) backend** with **vanilla JS Canvas frontend**.

**Rationale:**
- FastAPI runs on Hermes toolset without extra setup
- `numpy`/`scipy` already used in prior wood FEM POC
- `playwright-python` for auto-recording
- Canvas 2D sufficient for this viz level (no WebGL needed)
- Nix flake pins Python 3.11 + nodejs_20 + ffmpeg

## Consequences
- + Quick iteration, matrix math with numpy
- + Playwright video generation works out-of-box
- - Less type safety than Haskell/Rust
- - Frontend is imperative JS (not React/TS compiled)

## Notes
Haskell/Rust could be **revisited for solver engine** if we need GPU-accelerated large-scale FEM later. For now Python math is fast enough (solves <1ms for 100-node beam).
