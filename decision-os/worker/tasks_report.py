from __future__ import annotations

from report_engine.report_generator import generate_decision_report
from worker.celery_app import celery_app


@celery_app.task
def build_report(snapshot: dict) -> str:
    return generate_decision_report(snapshot)
