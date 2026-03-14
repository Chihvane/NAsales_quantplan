from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = ARTIFACTS_DIR / "decision_os_ui.db"


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS decision_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                factor_score REAL NOT NULL,
                profit_p10 REAL NOT NULL,
                profit_p50 REAL NOT NULL,
                profit_p90 REAL NOT NULL,
                loss_probability REAL NOT NULL,
                free_capital REAL NOT NULL,
                required_capital REAL NOT NULL,
                decision TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS report_exports (
                export_id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_markdown_path TEXT NOT NULL,
                report_html_path TEXT NOT NULL,
                report_pdf_path TEXT NOT NULL,
                decision TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_ref TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def save_decision_run(snapshot: dict[str, Any]) -> int:
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO decision_runs (
                factor_score,
                profit_p10,
                profit_p50,
                profit_p90,
                loss_probability,
                free_capital,
                required_capital,
                decision,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot["factor_score"],
                snapshot["model_outputs"]["profit_p10"],
                snapshot["model_outputs"]["profit_p50"],
                snapshot["model_outputs"]["profit_p90"],
                snapshot["model_outputs"]["loss_probability"],
                snapshot["free_capital"],
                snapshot["required_capital"],
                snapshot["decision"],
                json.dumps(snapshot, ensure_ascii=False),
            ),
        )
        run_id = int(cursor.lastrowid)
        save_audit_event(
            event_type="decision_run",
            event_ref=f"decision_runs:{run_id}",
            payload={"decision": snapshot["decision"], "factor_score": snapshot["factor_score"]},
            connection=connection,
        )
        return run_id


def save_report_export(markdown_path: str, html_path: str, pdf_path: str, decision: str) -> int:
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO report_exports (
                report_markdown_path,
                report_html_path,
                report_pdf_path,
                decision
            ) VALUES (?, ?, ?, ?)
            """,
            (markdown_path, html_path, pdf_path, decision),
        )
        export_id = int(cursor.lastrowid)
        save_audit_event(
            event_type="report_export",
            event_ref=f"report_exports:{export_id}",
            payload={"decision": decision, "report_pdf_path": pdf_path},
            connection=connection,
        )
        return export_id


def save_audit_event(
    event_type: str,
    event_ref: str,
    payload: dict[str, Any],
    connection: sqlite3.Connection | None = None,
) -> int:
    owns_connection = connection is None
    connection = connection or _connect()
    cursor = connection.execute(
        """
        INSERT INTO audit_events (
            event_type,
            event_ref,
            payload_json
        ) VALUES (?, ?, ?)
        """,
        (event_type, event_ref, json.dumps(payload, ensure_ascii=False)),
    )
    if owns_connection:
        connection.commit()
        connection.close()
    return int(cursor.lastrowid)


def list_recent_decisions(limit: int = 10) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT run_id, factor_score, profit_p50, loss_probability, free_capital, required_capital, decision, created_at
            FROM decision_runs
            ORDER BY run_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_recent_audit_events(limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT event_id, event_type, event_ref, payload_json, created_at
            FROM audit_events
            ORDER BY event_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    payloads = []
    for row in rows:
        item = dict(row)
        item["payload_json"] = json.loads(item["payload_json"])
        payloads.append(item)
    return payloads


def list_recent_reports(limit: int = 10) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT export_id, report_markdown_path, report_html_path, report_pdf_path, decision, created_at
            FROM report_exports
            ORDER BY export_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
