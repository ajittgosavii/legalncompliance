"""
Regulatory Compliance AI - Database Layer
SQLite for prototype, PostgreSQL-ready schema for production.
"""

import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv("DATABASE_PATH", "./data/pwe_compliance.db")


@contextmanager
def get_db():
    """Context manager for database connections."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS regulatory_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                change_type TEXT,
                severity TEXT DEFAULT 'medium',
                url TEXT,
                published_date TEXT,
                detected_date TEXT DEFAULT CURRENT_TIMESTAMP,
                affected_departments TEXT,
                obligations_json TEXT,
                status TEXT DEFAULT 'new',
                reviewed_by TEXT,
                review_notes TEXT
            );

            CREATE TABLE IF NOT EXISTS obligations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regulation_id INTEGER,
                obligation_text TEXT NOT NULL,
                category TEXT,
                owner_department TEXT,
                deadline TEXT,
                compliance_status TEXT DEFAULT 'pending',
                impact_score REAL,
                cost_estimate REAL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                last_assessed TEXT,
                FOREIGN KEY (regulation_id) REFERENCES regulatory_changes(id)
            );

            CREATE TABLE IF NOT EXISTS audit_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_name TEXT NOT NULL,
                audit_type TEXT,
                regulation_ref TEXT,
                obligation_id INTEGER,
                evidence_status TEXT DEFAULT 'missing',
                evidence_path TEXT,
                gap_description TEXT,
                remediation_plan TEXT,
                due_date TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (obligation_id) REFERENCES obligations(id)
            );

            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_number TEXT UNIQUE,
                case_title TEXT NOT NULL,
                regulator TEXT,
                case_type TEXT,
                status TEXT,
                filing_date TEXT,
                resolution_date TEXT,
                penalty_amount REAL,
                summary TEXT,
                key_findings TEXT,
                precedent_tags TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS agent_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                run_id TEXT,
                status TEXT DEFAULT 'running',
                input_summary TEXT,
                output_summary TEXT,
                tokens_used INTEGER,
                cost_estimate REAL,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                trace_json TEXT
            );
        """)


def log_agent_run(agent_name: str, run_id: str, input_summary: str) -> int:
    """Log the start of an agent run."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO agent_runs (agent_name, run_id, input_summary) VALUES (?, ?, ?)",
            (agent_name, run_id, input_summary)
        )
        return cursor.lastrowid


def complete_agent_run(row_id: int, output_summary: str, tokens_used: int = 0, cost: float = 0.0):
    """Mark an agent run as completed."""
    with get_db() as conn:
        conn.execute(
            "UPDATE agent_runs SET status='completed', output_summary=?, tokens_used=?, cost_estimate=?, completed_at=? WHERE id=?",
            (output_summary, tokens_used, cost, datetime.utcnow().isoformat(), row_id)
        )


def save_regulatory_change(data: dict) -> int:
    """Save a detected regulatory change."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO regulatory_changes
               (source, title, summary, change_type, severity, url, published_date, affected_departments, obligations_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("source"), data.get("title"), data.get("summary"),
             data.get("change_type"), data.get("severity"), data.get("url"),
             data.get("published_date"), data.get("affected_departments"),
             json.dumps(data.get("obligations", [])))
        )
        return cursor.lastrowid


def get_recent_changes(limit: int = 20) -> list:
    """Get recent regulatory changes."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM regulatory_changes ORDER BY detected_date DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def save_obligation(data: dict) -> int:
    """Save an obligation record."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO obligations
               (regulation_id, obligation_text, category, owner_department, deadline, impact_score, cost_estimate)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (data.get("regulation_id"), data.get("obligation_text"), data.get("category"),
             data.get("owner_department"), data.get("deadline"),
             data.get("impact_score"), data.get("cost_estimate"))
        )
        return cursor.lastrowid


def get_obligations(status: str | None = None) -> list:
    """Get obligations, optionally filtered by status."""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM obligations WHERE compliance_status = ? ORDER BY deadline", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM obligations ORDER BY deadline").fetchall()
        return [dict(r) for r in rows]


def save_case(data: dict) -> int:
    """Save a case record."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT OR IGNORE INTO cases
               (case_number, case_title, regulator, case_type, status, filing_date,
                resolution_date, penalty_amount, summary, key_findings, precedent_tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("case_number"), data.get("case_title"), data.get("regulator"),
             data.get("case_type"), data.get("status"), data.get("filing_date"),
             data.get("resolution_date"), data.get("penalty_amount"),
             data.get("summary"), data.get("key_findings"), data.get("precedent_tags"))
        )
        return cursor.lastrowid
