# ADR-002: Data Persistence Strategy

## Status
Proposed

## Context
Need persistent storage for:
1. Bridge structure catalog (JSON, ~100 entries)
2. User simulation results (history, parameters)
3. Generated videos (MP4 files)

Current: all in-memory + filesystem.

Options:
1. **SQLite** — zero-setup, single file, Python stdlib `sqlite3`
2. **JSON file append** — simple but no query, race conditions
3. **PostgreSQL** — overkill for single-user local tool
4. **Haskell-inspired immutable event log** — write-once append log, replayable state

## Decision
Use **SQLite** for structured data + **filesystem** for video blobs.

**Schema sketch:**
```sql
CREATE TABLE simulations (
    id INTEGER PRIMARY KEY,
    bridge_id TEXT REFERENCES bridges(id),
    params JSON,
    sigma_max REAL,
    fractured BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_path TEXT
);

CREATE TABLE bridges (
    id TEXT PRIMARY KEY,
    category TEXT,
    name TEXT,
    params JSON  -- spans, materials, etc.
);
```

## Consequences
- + ACID guarantees for history
- + Queryable ("show all fractured simulations")
- + Works with Hermes session persistence
- - Slightly more code than json.dump

## Future: Haskell Event Sourcing
If state complexity grows, an append-only event log (Haskell/Eventstore style) could replace SQLite. Each `LoadApplied`, `FractureDetected` event logged, state replayable. Not needed now.
