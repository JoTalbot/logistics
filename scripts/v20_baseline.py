from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from logistics.commercial_replay import ReplayCase, evaluate_replay


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "commercial" / "v20_baseline.json"


def load_baseline(path: Path = FIXTURE) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    baseline = load_baseline()
    cases = [
        ReplayCase(
            case_id=item["case_id"],
            expected_minimum_price=Decimal(item["expected_minimum_price"]),
            observed_price=Decimal(item["observed_price"]),
            outcome=item["outcome"],
        )
        for item in baseline["replay_cases"]
    ]
    report = evaluate_replay(cases)
    print(json.dumps({"kpi_baseline": baseline["kpi_baseline"], "replay": report.__dict__}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
