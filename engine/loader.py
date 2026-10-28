"""
IntentLedger – Case loader.

Loads test cases from JSON files in tests/cases/.
"""

from __future__ import annotations

import json
from pathlib import Path

CASES_DIR = Path(__file__).parent.parent / "tests" / "cases"


def load_all_cases() -> list[dict]:
    """Load and return all test cases, sorted by filename."""
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            cases.append(json.load(f))
    return cases


def load_case(case_id: str) -> dict:
    """Load a single case by id."""
    for case in load_all_cases():
        if case["id"] == case_id:
            return case
    raise KeyError(f"Case not found: {case_id!r}")
