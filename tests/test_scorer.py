"""
Tests for engine.scorer – comparison logic and scoring.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.scorer import score, summarise, ScoreResult


# ---------------------------------------------------------------------------
# Basic match / mismatch
# ---------------------------------------------------------------------------

def test_exact_match():
    result = score(
        case_id="test",
        mode="improved",
        expected={"action": "book", "restaurant": "Bella Italia", "party_size": 4},
        predicted={"action": "book", "restaurant": "Bella Italia", "party_size": 4},
    )
    assert result.verdict == "PASS"
    assert result.matched == 3
    assert result.mismatched == 0
    assert result.missing == 0
    assert result.field_match_rate == 1.0


def test_mismatch_gives_fail():
    result = score(
        case_id="test",
        mode="improved",
        expected={"time": "3:00 PM"},
        predicted={"time": "2:00 PM"},
    )
    assert result.verdict == "FAIL"
    assert result.mismatched == 1
    assert result.matched == 0


def test_missing_field_gives_fail():
    result = score(
        case_id="test",
        mode="improved",
        expected={"action": "book", "location": "Room A"},
        predicted={"action": "book"},
    )
    assert result.verdict == "FAIL"
    assert result.missing == 1


def test_unexpected_field_does_not_fail():
    """Extra predicted fields are flagged but do not count as FAIL on their own."""
    result = score(
        case_id="test",
        mode="improved",
        expected={"action": "book"},
        predicted={"action": "book", "extra": "value"},
    )
    assert result.verdict == "PASS"
    assert result.unexpected == 1


def test_none_prediction_is_error():
    result = score(
        case_id="test",
        mode="baseline",
        expected={"action": "book"},
        predicted=None,
        error_message="model failed",
    )
    assert result.verdict == "ERROR"
    assert "model failed" in result.error_message


# ---------------------------------------------------------------------------
# Time normalisation through scorer
# ---------------------------------------------------------------------------

def test_time_normalization_passes():
    """'3pm' and '3:00 PM' should normalise to the same canonical value."""
    result = score(
        case_id="test",
        mode="improved",
        expected={"time": "3:00 PM"},
        predicted={"time": "3pm"},
    )
    assert result.verdict == "PASS", (
        f"Expected PASS but got {result.verdict}. "
        f"Fields: {result.field_results}"
    )


def test_budget_normalization_passes():
    """'$3,000' and 3000 should normalise to the same canonical value."""
    result = score(
        case_id="test",
        mode="improved",
        expected={"budget_usd": 3000},
        predicted={"budget_usd": "$3,000"},
    )
    assert result.verdict == "PASS"


# ---------------------------------------------------------------------------
# Clarification metric
# ---------------------------------------------------------------------------

def test_clarification_required_and_present():
    result = score(
        case_id="ambiguous",
        mode="improved",
        expected={"action": "logo_redesign", "clarification_needed": True},
        predicted={"action": "logo_redesign", "clarification_needed": True},
        clarification_expected=True,
    )
    assert result.verdict == "PASS"
    assert result.clarification_ok is True


def test_clarification_required_but_missing():
    result = score(
        case_id="ambiguous",
        mode="baseline",
        expected={"action": "logo_redesign", "clarification_needed": True},
        predicted={"action": "logo_redesign", "clarification_needed": False},
        clarification_expected=True,
    )
    assert result.verdict == "FAIL"
    assert result.clarification_ok is False


# ---------------------------------------------------------------------------
# Summarise
# ---------------------------------------------------------------------------

def test_summarise_empty():
    assert summarise([]) == {}


def test_summarise_mixed():
    r1 = score("a", "improved", {"x": 1}, {"x": 1})
    r2 = score("b", "improved", {"x": 1}, {"x": 2})
    r3 = score("c", "improved", {"x": 1}, None, error_message="err")

    summary = summarise([r1, r2, r3])
    assert summary["total"] == 3
    assert summary["passes"] == 1
    assert summary["fails"] == 1
    assert summary["errors"] == 1
    assert 0.0 <= summary["avg_field_match_rate"] <= 1.0


def test_field_match_rate_partial():
    result = score(
        case_id="test",
        mode="improved",
        expected={"a": 1, "b": 2, "c": 3, "d": 4},
        predicted={"a": 1, "b": 2, "c": 99, "d": 99},
    )
    assert result.field_match_rate == pytest.approx(0.5)
    assert result.matched == 2
    assert result.mismatched == 2
