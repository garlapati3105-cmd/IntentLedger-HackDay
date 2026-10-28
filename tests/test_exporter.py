"""Tests for JSON and CSV evaluation-result exports."""

import csv
import io
import json
from datetime import datetime, timezone

from engine.exporter import (
    CSV_COLUMNS,
    build_export_bundle,
    export_csv,
    export_json,
)
from engine.scorer import score


FIXED_TIME = datetime(2026, 10, 28, 8, 0, tzinfo=timezone.utc)

CASES = [
    {
        "id": "case_one",
        "name": "Quoted, Unicode Scenario – 東京",
        "expected_state": {
            "action": "book",
            "details": {"note": 'Line one, "quoted"\nLine two', "tags": ["café", "東京"]},
        },
    },
    {
        "id": "case_two",
        "name": "Second Case",
        "expected_state": {"action": "cancel", "status": "cancelled"},
    },
]


def successful_result(case, mode="baseline"):
    return score(
        case_id=case["id"],
        mode=mode,
        expected=case["expected_state"],
        predicted=case["expected_state"].copy(),
    )


def bundle(baseline=None, improved=None):
    return build_export_bundle(
        CASES,
        baseline or {},
        improved or {},
        "gemma-4-26b-a4b-it",
        exported_at=FIXED_TIME,
    )


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def test_export_successful_result_as_structured_json():
    result = successful_result(CASES[0])
    exported = bundle({CASES[0]["id"]: result})
    encoded = export_json(exported)
    decoded = json.loads(encoded)

    assert decoded["export_format_version"] == "1.0"
    assert decoded["exported_at"] == "2026-10-28T08:00:00Z"
    assert decoded["model_id"] == "gemma-4-26b-a4b-it"
    assert decoded["result_count"] == 1
    record = decoded["results"][0]
    assert record["verdict"] == "PASS"
    assert record["predicted_state"] == CASES[0]["expected_state"]
    assert record["field_match_rate"] == 1.0
    assert record["error"] is None


def test_export_both_baseline_and_improved_results():
    baseline = successful_result(CASES[0], "baseline")
    improved = successful_result(CASES[0], "improved")
    exported = bundle({"case_one": baseline}, {"case_one": improved})

    assert exported["result_count"] == 2
    assert [record["prompt_mode"] for record in exported["results"]] == [
        "baseline",
        "improved",
    ]


def test_export_only_available_mode_without_fabricating_missing_result():
    improved = successful_result(CASES[1], "improved")
    exported = bundle(improved={"case_two": improved})

    assert exported["result_count"] == 1
    assert exported["results"][0]["scenario_id"] == "case_two"
    assert exported["results"][0]["prompt_mode"] == "improved"
    assert all(record["prompt_mode"] != "baseline" for record in exported["results"])


def test_export_error_result_preserves_classification_and_redacts_secret():
    result = score(
        case_id="case_one",
        mode="baseline",
        expected=CASES[0]["expected_state"],
        predicted=None,
        error_message="OFFLINE MODE – no model call was made. api_key=AIzaSecretValue123456789012345",
    )
    record = bundle({"case_one": result})["results"][0]

    assert record["verdict"] == "ERROR"
    assert record["field_match_rate"] is None
    assert record["error"]["type"] == "offline_mode"
    assert "AIzaSecretValue" not in record["error"]["message"]
    assert "[REDACTED]" in record["error"]["message"]
    assert record["predicted_state"] is None


def test_export_sanitizes_credential_environment_variable_name():
    result = score(
        case_id="case_one",
        mode="baseline",
        expected=CASES[0]["expected_state"],
        predicted=None,
        error_message="Set GEMINI_API_KEY to enable live evaluation.",
    )
    exported = export_json(bundle({"case_one": result})).decode("utf-8")

    assert "GEMINI_API_KEY" not in exported
    assert "credential environment variable" in exported


def test_empty_result_collection_has_no_fabricated_records():
    exported = bundle()
    assert exported["result_count"] == 0
    assert exported["results"] == []
    assert csv_rows(export_csv(exported)) == []


def test_nested_expected_and_predicted_state_remain_structured():
    result = successful_result(CASES[0])
    record = json.loads(export_json(bundle({"case_one": result})))["results"][0]

    assert isinstance(record["expected_state"]["details"], dict)
    assert isinstance(record["predicted_state"]["details"]["tags"], list)
    assert record["predicted_state"]["details"]["tags"][1] == "東京"


def test_csv_columns_and_nested_json_cells_are_valid():
    result = successful_result(CASES[0])
    rows = csv_rows(export_csv(bundle({"case_one": result})))

    assert tuple(rows[0].keys()) == CSV_COLUMNS
    expected = json.loads(rows[0]["expected_state_json"])
    predicted = json.loads(rows[0]["predicted_state_json"])
    assert expected == CASES[0]["expected_state"]
    assert predicted == CASES[0]["expected_state"]


def test_csv_escapes_commas_quotes_newlines_and_unicode():
    result = successful_result(CASES[0])
    raw = export_csv(bundle({"case_one": result}))
    rows = csv_rows(raw)

    assert len(rows) == 1
    assert rows[0]["scenario_name"] == "Quoted, Unicode Scenario – 東京"
    details = json.loads(rows[0]["predicted_state_json"])["details"]
    assert details["note"] == 'Line one, "quoted"\nLine two'
    assert details["tags"] == ["café", "東京"]


def test_export_contains_no_api_key_or_raw_secret_configuration():
    result = successful_result(CASES[1])
    json_text = export_json(bundle({"case_two": result})).decode("utf-8")
    csv_text = export_csv(bundle({"case_two": result})).decode("utf-8-sig")

    assert "GEMINI_API_KEY" not in json_text
    assert "GEMINI_API_KEY" not in csv_text
    assert "api_key" not in json_text.lower()
    assert "api_key" not in csv_text.lower()


def test_optional_absent_prediction_is_safe_in_csv():
    result = score(
        case_id="case_two",
        mode="improved",
        expected=CASES[1]["expected_state"],
        predicted=None,
        error_message="Model returned non-JSON output",
    )
    row = csv_rows(export_csv(bundle(improved={"case_two": result})))[0]

    assert row["predicted_state_json"] == ""
    assert row["error_type"] == "invalid_response"
    assert row["verdict"] == "ERROR"


def test_field_comparisons_and_counts_are_exported():
    result = score(
        case_id="case_two",
        mode="baseline",
        expected=CASES[1]["expected_state"],
        predicted={"action": "cancel", "status": "active", "extra": True},
    )
    record = bundle({"case_two": result})["results"][0]

    assert record["counts"] == {
        "matched": 1,
        "mismatched": 1,
        "missing": 0,
        "unexpected": 1,
    }
    assert {field["status"] for field in record["field_comparisons"]} == {
        "match",
        "mismatch",
        "unexpected",
    }
