from __future__ import annotations


def sample_evidence_graph() -> dict:
    return {
        "nodes": ["field", "metric", "factor", "model", "gate"],
        "edges": [("field", "metric"), ("metric", "factor"), ("factor", "model"), ("model", "gate")],
    }
