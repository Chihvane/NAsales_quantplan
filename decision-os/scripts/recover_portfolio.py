from __future__ import annotations

import json
import sys


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python recover_portfolio.py <decision_id>")
    decision_id = sys.argv[1]
    print(json.dumps({"decision_id": decision_id, "action": "recover_portfolio_snapshot"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
