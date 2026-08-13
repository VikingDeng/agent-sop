#!/usr/bin/env python3
"""Frozen receipt reader used by the Phase 0 runner.

It cannot rerun the experiment and must never rewrite raw evidence.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_receipts() -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    with (ROOT / "raw-results.csv").open(newline="", encoding="utf-8") as handle:
        results = list(csv.DictReader(handle))
    with (ROOT / "run-order.json").open(encoding="utf-8") as handle:
        order = json.load(handle)["events"]
    return results, order


if __name__ == "__main__":
    result_rows, order_events = load_receipts()
    print(json.dumps({"result_rows": len(result_rows), "order_events": len(order_events)}, sort_keys=True))
