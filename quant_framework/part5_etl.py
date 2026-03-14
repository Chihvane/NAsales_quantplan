from __future__ import annotations

import hashlib
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from .io_utils import read_csv_rows, write_csv_rows, write_json
from .part5_pipeline import build_part5_dataset_from_directory


PART5_REQUIRED_TABLES = [
    "listing_snapshots.csv",
    "sold_transactions.csv",
    "product_catalog.csv",
    "landed_cost_scenarios.csv",
    "channel_rate_cards.csv",
    "marketing_spend.csv",
    "traffic_sessions.csv",
    "returns_claims.csv",
    "customer_cohorts.csv",
    "inventory_positions.csv",
    "experiment_registry.csv",
    "b2b_accounts.csv",
    "kpi_daily_snapshots.csv",
    "pricing_actions.csv",
    "reorder_plan.csv",
    "policy_change_log.csv",
    "cash_flow_snapshots.csv",
]

PART5_OPTIONAL_TABLES = [
    "experiment_assignments.csv",
    "experiment_metrics.csv",
]

PART5_CONNECTOR_TYPES = {
    "bundle_sync": {
        "supports_incremental": True,
        "description": "Copy an already-exported local Part 5 bundle into ETL raw/curated layers.",
    },
    "export_drop": {
        "supports_incremental": True,
        "description": "Ingest a local folder that simulates a manual platform export drop.",
    },
    "api_cache": {
        "supports_incremental": False,
        "description": "Ingest a cached API payload directory without direct network access.",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _csv_fieldnames(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = handle.readline().strip()
    return header.split(",") if header else []


def _copy_into(src: Path, dst: Path) -> dict:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    rows = read_csv_rows(dst) if dst.suffix.lower() == ".csv" else []
    return {
        "file_name": dst.name,
        "bytes": dst.stat().st_size,
        "sha256": _sha256(dst),
        "record_count": len(rows),
    }


def _copy_with_retries(
    src: Path,
    dst: Path,
    max_retries: int = 3,
    connector: str = "bundle_sync",
) -> dict:
    attempt_logs = []
    last_error = ""
    for attempt in range(1, max_retries + 1):
        started_at = datetime.now(timezone.utc).isoformat()
        try:
            file_summary = _copy_into(src, dst)
            attempt_logs.append(
                {
                    "attempt": attempt,
                    "status": "success",
                    "started_at": started_at,
                    "connector": connector,
                    "file_name": src.name,
                }
            )
            file_summary["attempts"] = attempt
            file_summary["attempt_logs"] = attempt_logs
            return file_summary
        except OSError as exc:
            last_error = str(exc)
            attempt_logs.append(
                {
                    "attempt": attempt,
                    "status": "retry",
                    "started_at": started_at,
                    "connector": connector,
                    "file_name": src.name,
                    "error": last_error,
                }
            )
            if attempt < max_retries:
                time.sleep(min(0.05 * attempt, 0.2))
    raise OSError(f"Failed to stage {src.name} after {max_retries} attempts: {last_error}")


def _manifest_files_by_name(manifest_path: str | Path | None) -> dict[str, dict]:
    if manifest_path is None:
        return {}
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return {}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = payload.get("curated", {}).get("files", [])
    return {
        row["file_name"]: row
        for row in files
        if isinstance(row, dict) and row.get("file_name")
    }


def _detect_previous_manifest(audit_dir: Path, current_batch_id: str) -> Path | None:
    manifest_paths = sorted(audit_dir.glob("part5_etl_manifest_*.json"))
    eligible = [
        path for path in manifest_paths
        if path.stem != f"part5_etl_manifest_{current_batch_id}"
    ]
    return eligible[-1] if eligible else None


def _build_manifest_diff(
    current_files: list[dict],
    previous_manifest_path: str | Path | None,
) -> dict:
    previous_files = _manifest_files_by_name(previous_manifest_path)
    current_lookup = {row["file_name"]: row for row in current_files}
    added = sorted(name for name in current_lookup if name not in previous_files)
    removed = sorted(name for name in previous_files if name not in current_lookup)
    changed = []
    unchanged = []
    for file_name, current in current_lookup.items():
        previous = previous_files.get(file_name)
        if previous is None:
            continue
        if current.get("sha256") != previous.get("sha256"):
            changed.append(
                {
                    "file_name": file_name,
                    "record_delta": current.get("record_count", 0) - previous.get("record_count", 0),
                    "bytes_delta": current.get("bytes", 0) - previous.get("bytes", 0),
                }
            )
        else:
            unchanged.append(file_name)
    return {
        "previous_manifest": str(previous_manifest_path) if previous_manifest_path else "",
        "added_files": added,
        "removed_files": removed,
        "changed_files": changed,
        "unchanged_files": sorted(unchanged),
    }


def stage_part5_raw_bundle(
    source_dir: str | Path,
    raw_dir: str | Path,
    connector: str = "bundle_sync",
    max_retries: int = 3,
) -> dict:
    source_dir = Path(source_dir)
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    if connector not in PART5_CONNECTOR_TYPES:
        raise ValueError(f"Unsupported Part 5 connector: {connector}")

    staged_files = []
    staging_log = []
    for path in sorted(source_dir.glob("*")):
        if path.is_file() and path.suffix.lower() in {".csv", ".json"}:
            file_summary = _copy_with_retries(
                path,
                raw_dir / path.name,
                max_retries=max_retries,
                connector=connector,
            )
            staged_files.append(file_summary)
            staging_log.extend(file_summary.get("attempt_logs", []))
    return {
        "raw_dir": str(raw_dir),
        "connector": connector,
        "connector_metadata": PART5_CONNECTOR_TYPES[connector],
        "staged_files": staged_files,
        "staging_log": staging_log,
    }


def materialize_part5_curated_bundle(source_dir: str | Path, curated_dir: str | Path) -> dict:
    source_dir = Path(source_dir)
    curated_dir = Path(curated_dir)
    curated_dir.mkdir(parents=True, exist_ok=True)

    missing_required = [name for name in PART5_REQUIRED_TABLES if not (source_dir / name).exists()]
    if missing_required:
        raise FileNotFoundError(f"Missing required Part 5 source tables: {', '.join(missing_required)}")

    manifests = []
    for name in PART5_REQUIRED_TABLES + PART5_OPTIONAL_TABLES:
        src = source_dir / name
        if not src.exists():
            continue
        rows = read_csv_rows(src)
        fieldnames = _csv_fieldnames(src)
        dst = curated_dir / name
        write_csv_rows(dst, fieldnames, rows)
        manifests.append(
            {
                "file_name": name,
                "bytes": dst.stat().st_size,
                "sha256": _sha256(dst),
                "record_count": len(rows),
            }
        )

    dataset = build_part5_dataset_from_directory(curated_dir)
    return {
        "curated_dir": str(curated_dir),
        "files": manifests,
        "table_inventory": {
            field: len(value) if hasattr(value, "__len__") else None
            for field, value in dataset.__dict__.items()
        },
    }


def run_part5_etl_skeleton(
    source_dir: str | Path,
    output_dir: str | Path,
    batch_id: str | None = None,
    connector: str = "bundle_sync",
    max_retries: int = 3,
    previous_manifest: str | Path | None = None,
) -> dict:
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    batch_id = batch_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    raw_dir = output_dir / "raw" / batch_id
    curated_dir = output_dir / "curated" / batch_id
    audit_dir = output_dir / "audit"

    raw_summary = stage_part5_raw_bundle(
        source_dir,
        raw_dir,
        connector=connector,
        max_retries=max_retries,
    )
    curated_summary = materialize_part5_curated_bundle(source_dir, curated_dir)
    previous_manifest_path = Path(previous_manifest) if previous_manifest else _detect_previous_manifest(audit_dir, batch_id)
    manifest_diff = _build_manifest_diff(
        curated_summary["files"],
        previous_manifest_path,
    )
    run_log = {
        "batch_id": batch_id,
        "connector": connector,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "max_retries": max_retries,
        "staged_file_count": len(raw_summary["staged_files"]),
        "staging_log": raw_summary.get("staging_log", []),
        "manifest_diff": manifest_diff,
    }
    manifest = {
        "batch_id": batch_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source_dir),
        "connector": connector,
        "connector_metadata": PART5_CONNECTOR_TYPES[connector],
        "required_tables": PART5_REQUIRED_TABLES,
        "optional_tables": PART5_OPTIONAL_TABLES,
        "raw": raw_summary,
        "curated": curated_summary,
        "manifest_diff": manifest_diff,
    }
    manifest_path = write_json(audit_dir / f"part5_etl_manifest_{batch_id}.json", manifest)
    run_log_path = write_json(audit_dir / f"part5_etl_run_log_{batch_id}.json", run_log)
    return {
        "batch_id": batch_id,
        "raw_dir": str(raw_dir),
        "curated_dir": str(curated_dir),
        "manifest_json": str(manifest_path),
        "run_log_json": str(run_log_path),
    }
