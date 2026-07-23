-- bridge100 SQLite schema
-- Compatible with Python sqlite3 stdlib

CREATE TABLE IF NOT EXISTS bridges (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    params_json TEXT NOT NULL  -- JSON string of all mechanical params
);

CREATE TABLE IF NOT EXISTS simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bridge_id TEXT REFERENCES bridges(id),
    params_json TEXT NOT NULL,  -- user inputs: L, b, h, E, P, support
    results_json TEXT NOT NULL, -- sigma_max, delta, fractured, etc.
    sigma_ratio REAL,
    fractured BOOLEAN,
    video_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sim_bridge ON simulations(bridge_id);
CREATE INDEX IF NOT EXISTS idx_sim_fractured ON simulations(fractured);

-- Insert seed data from bridge_structures.json via Python loader
