from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decision_os_v3.demo import run_decision_os_v3_demo  # noqa: E402


def main() -> None:
    output_dir = ROOT / "examples" / "output_decision_os_v3"
    payload = run_decision_os_v3_demo(output_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
