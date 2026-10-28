"""
IntentLedger – Scorer.

Compares a predicted JSON state against an expected JSON state and
produces a detailed, field-level result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.normalizer import normalize


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FieldResult:
    key: str
    status: str          # "match" | "mismatch" | "missing" | "unexpected"
    expected: Any = None
    predicted: Any = None
    expected_norm: Any = None
    predicted_norm: Any = None


@dataclass
class ScoreResult:
    case_id: str
    mode: str
    verdict: str                            # "PASS" | "FAIL" | "ERROR"
    field_results: list[FieldResult] = field(default_factory=list)
    field_match_rate: float = 0.0
    matched: int = 0
    mismatched: int = 0
    missing: int = 0
    unexpected: int = 0
    total_expected: int = 0
    clarification_ok: bool | None = None    # None if not applicable
    clarification_expected: bool = False
    error_message: str = ""
    raw_prediction: str = ""                # Raw model output for inspection
    predicted_state: dict | None = None      # Parsed model state for export


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------

def score(
    case_id: str,
    mode: str,
    expected: dict,
    predicted: dict | None,
    clarification_expected: bool = False,
    error_message: str = "",
    raw_prediction: str = "",
) -> ScoreResult:
    """
    Score a prediction against the expected state.

    Args:
        case_id: identifier for the test case
        mode: 'baseline' or 'improved'
        expected: ground-truth dict
        predicted: model-output dict (None on parse error)
        clarification_expected: whether this case requires clarification behaviour
        error_message: populated when an upstream error occurred
        raw_prediction: raw string from the model for UI display

    Returns:
        ScoreResult with full field-level breakdown
    """
    result = ScoreResult(
        case_id=case_id,
        mode=mode,
        verdict="PASS",
        clarification_expected=clarification_expected,
        raw_prediction=raw_prediction,
        error_message=error_message,
        predicted_state=predicted.copy() if isinstance(predicted, dict) else None,
    )

    # --- ERROR path ---
    if predicted is None:
        result.verdict = "ERROR"
        result.error_message = error_message or "No prediction (model call failed or JSON invalid)"
        return result

    result.total_expected = len(expected)
    field_results: list[FieldResult] = []

    # --- Per-field comparison on expected keys ---
    for key, exp_val in expected.items():
        exp_norm = normalize(exp_val)
        pred_val = predicted.get(key)

        if pred_val is None:
            field_results.append(FieldResult(
                key=key, status="missing",
                expected=exp_val, predicted=None,
                expected_norm=exp_norm, predicted_norm=None,
            ))
            result.missing += 1
        else:
            pred_norm = normalize(pred_val)
            if exp_norm == pred_norm:
                field_results.append(FieldResult(
                    key=key, status="match",
                    expected=exp_val, predicted=pred_val,
                    expected_norm=exp_norm, predicted_norm=pred_norm,
                ))
                result.matched += 1
            else:
                field_results.append(FieldResult(
                    key=key, status="mismatch",
                    expected=exp_val, predicted=pred_val,
                    expected_norm=exp_norm, predicted_norm=pred_norm,
                ))
                result.mismatched += 1

    # --- Unexpected keys (predicted but not in expected) ---
    for key, pred_val in predicted.items():
        if key not in expected:
            field_results.append(FieldResult(
                key=key, status="unexpected",
                expected=None, predicted=pred_val,
                expected_norm=None, predicted_norm=normalize(pred_val),
            ))
            result.unexpected += 1

    result.field_results = field_results

    # --- Field match rate ---
    if result.total_expected > 0:
        result.field_match_rate = result.matched / result.total_expected
    else:
        result.field_match_rate = 1.0

    # --- Clarification metric for the ambiguous case ---
    if clarification_expected:
        pred_clr = predicted.get("clarification_needed")
        result.clarification_ok = bool(pred_clr) is True or str(pred_clr).lower() == "true"

    # --- Overall verdict ---
    if result.mismatched > 0 or result.missing > 0:
        result.verdict = "FAIL"
    elif clarification_expected and not result.clarification_ok:
        result.verdict = "FAIL"
    else:
        result.verdict = "PASS"

    return result


# ---------------------------------------------------------------------------
# Aggregate summary across multiple results
# ---------------------------------------------------------------------------

def summarise(results: list[ScoreResult]) -> dict:
    """Return aggregate stats across a list of ScoreResult objects."""
    if not results:
        return {}

    total = len(results)
    passes = sum(1 for r in results if r.verdict == "PASS")
    fails = sum(1 for r in results if r.verdict == "FAIL")
    errors = sum(1 for r in results if r.verdict == "ERROR")

    match_rates = [r.field_match_rate for r in results if r.verdict != "ERROR"]
    avg_match_rate = sum(match_rates) / len(match_rates) if match_rates else 0.0

    return {
        "total": total,
        "passes": passes,
        "fails": fails,
        "errors": errors,
        "avg_field_match_rate": avg_match_rate,
        "pass_rate": passes / total if total else 0.0,
    }
