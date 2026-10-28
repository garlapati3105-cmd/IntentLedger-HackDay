"""Serialization helpers for exporting IntentLedger evaluation results."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping

from engine.scorer import FieldResult, ScoreResult

EXPORT_FORMAT_VERSION = "1.0"

CSV_COLUMNS = (
    "scenario_id",
    "scenario_name",
    "model_id",
    "prompt_mode",
    "verdict",
    "field_match_rate",
    "matched_count",
    "mismatched_count",
    "missing_count",
    "unexpected_count",
    "expected_state_json",
    "predicted_state_json",
    "error_type",
    "error_message",
)

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_ -]?key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s,;]+)"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
)


def sanitize_error_message(message: str) -> str:
    """Redact common credential shapes while retaining useful diagnostics."""
    sanitized = str(message or "")
    sanitized = re.sub(
        r"(?i)\bGEMINI_API_KEY\b",
        "[credential environment variable]",
        sanitized,
    )
    sanitized = _SECRET_PATTERNS[0].sub(r"\1[REDACTED]", sanitized)
    sanitized = _SECRET_PATTERNS[1].sub(r"\1[REDACTED]", sanitized)
    sanitized = _SECRET_PATTERNS[2].sub("[REDACTED]", sanitized)
    return sanitized


def classify_error(message: str) -> str:
    """Return a stable export classification for an existing ERROR result."""
    lowered = str(message or "").lower()
    if not lowered:
        return "unknown_error"
    if "offline mode" in lowered or "no api key" in lowered:
        return "offline_mode"
    if "quota" in lowered or "429" in lowered:
        return "quota_exceeded"
    if "invalid api key" in lowered:
        return "invalid_api_key"
    if "model not found" in lowered or "404" in lowered:
        return "model_not_found"
    if "package not installed" in lowered:
        return "dependency_missing"
    if "non-json" in lowered or "no prediction" in lowered:
        return "invalid_response"
    if "model call failed" in lowered:
        return "model_call_failed"
    return "unknown_error"


def _field_record(field: FieldResult) -> dict[str, Any]:
    return {
        "field": field.key,
        "status": field.status,
        "expected": field.expected,
        "predicted": field.predicted,
    }


def _result_record(
    case: Mapping[str, Any],
    result: ScoreResult,
    model_id: str,
) -> dict[str, Any]:
    is_error = result.verdict == "ERROR"
    return {
        "scenario_id": result.case_id,
        "scenario_name": case.get("name", result.case_id),
        "model_id": model_id,
        "prompt_mode": result.mode,
        "expected_state": case.get("expected_state", {}),
        "predicted_state": result.predicted_state,
        "field_comparisons": [_field_record(field) for field in result.field_results],
        "counts": {
            "matched": result.matched,
            "mismatched": result.mismatched,
            "missing": result.missing,
            "unexpected": result.unexpected,
        },
        "field_match_rate": result.field_match_rate if not is_error else None,
        "verdict": result.verdict,
        "error": {
            "type": classify_error(result.error_message),
            "message": sanitize_error_message(result.error_message),
        } if is_error else None,
    }


def build_export_bundle(
    cases: list[Mapping[str, Any]],
    baseline_results: Mapping[str, ScoreResult],
    improved_results: Mapping[str, ScoreResult],
    model_id: str,
    *,
    exported_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a structured export containing only results that actually exist."""
    case_map = {str(case["id"]): case for case in cases}
    timestamp = exported_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    records: list[dict[str, Any]] = []
    for mode_results in (baseline_results, improved_results):
        for case in cases:
            case_id = str(case["id"])
            result = mode_results.get(case_id)
            if result is not None:
                records.append(_result_record(case, result, model_id))

        # Preserve valid stored results even if a future case list changes.
        known_ids = {str(case["id"]) for case in cases}
        for case_id, result in mode_results.items():
            if case_id not in known_ids:
                records.append(_result_record(case_map.get(case_id, {"name": case_id}), result, model_id))

    return {
        "export_format_version": EXPORT_FORMAT_VERSION,
        "exported_at": timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model_id": model_id,
        "available_scenarios": [
            {"scenario_id": case["id"], "scenario_name": case.get("name", case["id"])}
            for case in cases
        ],
        "result_count": len(records),
        "results": records,
    }


def export_json(bundle: Mapping[str, Any]) -> bytes:
    """Serialize an export bundle as UTF-8 formatted JSON."""
    return json.dumps(bundle, ensure_ascii=False, indent=2).encode("utf-8")


def export_csv(bundle: Mapping[str, Any]) -> bytes:
    """Serialize export records as RFC-compatible UTF-8 CSV."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for record in bundle.get("results", []):
        counts = record.get("counts") or {}
        error = record.get("error") or {}
        writer.writerow({
            "scenario_id": record.get("scenario_id", ""),
            "scenario_name": record.get("scenario_name", ""),
            "model_id": record.get("model_id", ""),
            "prompt_mode": record.get("prompt_mode", ""),
            "verdict": record.get("verdict", ""),
            "field_match_rate": "" if record.get("field_match_rate") is None else record["field_match_rate"],
            "matched_count": counts.get("matched", 0),
            "mismatched_count": counts.get("mismatched", 0),
            "missing_count": counts.get("missing", 0),
            "unexpected_count": counts.get("unexpected", 0),
            "expected_state_json": json.dumps(record.get("expected_state", {}), ensure_ascii=False),
            "predicted_state_json": "" if record.get("predicted_state") is None else json.dumps(record["predicted_state"], ensure_ascii=False),
            "error_type": error.get("type", ""),
            "error_message": error.get("message", ""),
        })
    return output.getvalue().encode("utf-8-sig")
