"""Atomic, versioned initialization. Existing unknown databases are never migrated implicitly."""

SCHEMA_VERSION = 1
APPLICATION_ID = 0x43545831
TABLES = frozenset({"incidents", "analysis_runs", "evidence", "agent_runs", "audit_events"})
STATEMENTS = (
    """CREATE TABLE incidents (
        incident_id TEXT PRIMARY KEY, asset_id TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('open', 'investigating', 'closed')),
        revision INTEGER NOT NULL CHECK(revision >= 1),
        created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""",
    """CREATE TABLE analysis_runs (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL UNIQUE,
        incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
        recorded_at TEXT NOT NULL, engine_version TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('completed', 'blocked')),
        report_status TEXT CHECK(report_status IN ('clear', 'needs_review', 'insufficient_data')),
        replay_of TEXT REFERENCES analysis_runs(run_id),
        payload TEXT NOT NULL, checksum TEXT NOT NULL)""",
    """CREATE TABLE evidence (
        run_id TEXT NOT NULL REFERENCES analysis_runs(run_id),
        ordinal INTEGER NOT NULL, evidence_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        PRIMARY KEY(run_id, evidence_id), UNIQUE(run_id, ordinal))""",
    """CREATE TABLE agent_runs (
        run_id TEXT NOT NULL REFERENCES analysis_runs(run_id),
        ordinal INTEGER NOT NULL, task_id TEXT NOT NULL,
        payload TEXT NOT NULL,
        PRIMARY KEY(run_id, task_id), UNIQUE(run_id, ordinal))""",
    """CREATE TABLE audit_events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
        run_id TEXT REFERENCES analysis_runs(run_id), recorded_at TEXT NOT NULL,
        actor TEXT NOT NULL,
        action TEXT NOT NULL CHECK(action IN ('incident_created', 'analysis_saved', 'status_changed')),
        old_status TEXT, new_status TEXT, reason TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision >= 1))""",
    "CREATE INDEX analysis_incident_order ON analysis_runs(incident_id, sequence DESC)",
    "CREATE INDEX audit_incident_order ON audit_events(incident_id, event_id DESC)",
    "CREATE INDEX incidents_status ON incidents(status)",
)
