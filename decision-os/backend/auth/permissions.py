from __future__ import annotations


def require_role(payload: dict, allowed_roles: set[str]) -> bool:
    return payload.get("role") in allowed_roles


def require_tenant(payload: dict, tenant_id: str) -> bool:
    return payload.get("tenant_id") == tenant_id


ROLE_MATRIX = {
    "analyst": {"gate": "read", "capital": "none", "risk": "none", "audit": "none"},
    "risk_officer": {"gate": "read", "capital": "read", "risk": "modify", "audit": "yes"},
    "strategy_director": {"gate": "approve", "capital": "modify", "risk": "modify", "audit": "yes"},
    "admin": {"gate": "full", "capital": "full", "risk": "full", "audit": "full"},
    "auditor": {"gate": "read", "capital": "read", "risk": "read", "audit": "full"},
}


def permission_for(role: str, domain: str) -> str:
    return ROLE_MATRIX.get(role, {}).get(domain, "none")
