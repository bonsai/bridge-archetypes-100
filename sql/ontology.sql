-- bridge-archetypes-100 ontology database schema
-- Relates structural engineering concepts in a graph-like triple store

-- Core entities
CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    label_en TEXT,
    category TEXT NOT NULL,  -- bridge_type | material | force | formula | exam_topic | component | phenomenon
    description TEXT NOT NULL,
    icon TEXT,  -- emoji
    difficulty INTEGER DEFAULT 1,  -- 1=beginner, 2=intermediate, 3=advanced
    exam_weight REAL,  -- 2級建築士出題頻度 0.0-1.0
    related_formulas TEXT,  -- JSON list of formula_ids
    properties_json TEXT  -- flexible attributes
);

-- Relationships (graph edges)
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id TEXT NOT NULL REFERENCES concepts(id),
    to_id TEXT NOT NULL REFERENCES concepts(id),
    rel_type TEXT NOT NULL,  -- has_material | applies_to | causes | resists | measured_by | part_of | example_of
    weight REAL DEFAULT 1.0,  -- strength of relationship
    context TEXT  -- e.g. "短期荷重時", "长期荷重時"
);

-- Formulas with parameter ontology
CREATE TABLE IF NOT EXISTS formulas (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_en TEXT,
    latex TEXT NOT NULL,
    variables_json TEXT NOT NULL,  -- [{"symbol":"σ","name":"曲げ応力度","unit":"MPa"}]
    conditions TEXT,  -- when this formula applies
    concepts_json TEXT  -- related concept IDs
);

-- Exam questions linked to ontology
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    concept_ids TEXT,  -- JSON list
    difficulty INTEGER,
    year INTEGER,  -- when it appeared
    source TEXT  -- e.g. "2級建築士H30"
);

-- Instances (bridge sim results become instances of archetypes)
CREATE TABLE IF NOT EXISTS instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archetype_id TEXT,
    params_json TEXT,
    results_json TEXT,
    concept_ids TEXT,  -- triggered concepts (e.g. fracture, buckling)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS concept_search USING fts5(label, description, content='concepts', content_rowid='rowid');

CREATE INDEX IF NOT EXISTS idx_rel_from ON relations(from_id);
CREATE INDEX IF NOT EXISTS idx_rel_to ON relations(to_id);
CREATE INDEX IF NOT EXISTS idx_concept_cat ON concepts(category);
