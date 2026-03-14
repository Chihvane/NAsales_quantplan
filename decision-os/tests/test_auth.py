from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.auth.jwt_handler import build_claims, create_token, verify_token  # noqa: E402
from backend.auth.permissions import require_role, require_tenant  # noqa: E402
from backend.auth.roles import ANALYST, AUDITOR  # noqa: E402


class AuthTests(unittest.TestCase):
    def test_jwt_claims_roundtrip(self) -> None:
        claims = build_claims("user-1", ANALYST, "tenant-1", 9999999999)
        token = create_token(claims)
        decoded = verify_token(token)
        self.assertEqual(decoded["tenant_id"], "tenant-1")
        self.assertTrue(require_role(decoded, {ANALYST, AUDITOR}))
        self.assertTrue(require_tenant(decoded, "tenant-1"))


if __name__ == "__main__":
    unittest.main()
