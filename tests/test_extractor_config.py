"""
Tests for engine.extractor configuration:
  - DEFAULT_MODEL constant value
  - _get_model_name() returns DEFAULT_MODEL when env var is absent
  - _get_model_name() returns the env-var value when INTENTLEDGER_MODEL is set
  - _get_api_key() returns None when GEMINI_API_KEY is unset or empty
  - _get_api_key() returns a stripped string when set
  - extract_state() returns OFFLINE_MODE_NOTE when no API key is present

No actual API calls are made in this file.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from engine.extractor import (
    API_KEY_ENV_VAR,
    DEFAULT_MODEL,
    MODEL_ENV_VAR,
    OFFLINE_MODE_NOTE,
    _get_api_key,
    _get_model_name,
    _extract_json_from_text,
    _strip_json_fences,
    extract_state,
)
from engine.prompts import build_extraction_prompt


# ---------------------------------------------------------------------------
# Default model constant
# ---------------------------------------------------------------------------

def test_default_model_is_gemma4():
    """DEFAULT_MODEL must be the hosted Gemma 4 model ID."""
    assert DEFAULT_MODEL == "gemma-4-26b-a4b-it", (
        f"Expected 'gemma-4-26b-a4b-it', got {DEFAULT_MODEL!r}"
    )


# ---------------------------------------------------------------------------
# _get_model_name – env-var override
# ---------------------------------------------------------------------------

def test_get_model_name_returns_default_when_env_absent(monkeypatch):
    """When INTENTLEDGER_MODEL is not set, _get_model_name returns DEFAULT_MODEL."""
    monkeypatch.delenv(MODEL_ENV_VAR, raising=False)
    assert _get_model_name() == DEFAULT_MODEL


def test_get_model_name_honours_env_override(monkeypatch):
    """When INTENTLEDGER_MODEL is set, _get_model_name returns that value."""
    monkeypatch.setenv(MODEL_ENV_VAR, "gemini-2.0-flash")
    assert _get_model_name() == "gemini-2.0-flash"


def test_get_model_name_honours_arbitrary_env_value(monkeypatch):
    """Env var override works for any model string, not just known ones."""
    monkeypatch.setenv(MODEL_ENV_VAR, "models/custom-test-model")
    assert _get_model_name() == "models/custom-test-model"


def test_get_model_name_ignores_empty_override(monkeypatch):
    """An empty override must not produce an invalid blank model name."""
    monkeypatch.setenv(MODEL_ENV_VAR, "   ")
    assert _get_model_name() == DEFAULT_MODEL


# ---------------------------------------------------------------------------
# _get_api_key – key handling (no real key used)
# ---------------------------------------------------------------------------

def test_get_api_key_returns_none_when_unset(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    assert _get_api_key() is None


def test_get_api_key_returns_none_when_empty(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "")
    assert _get_api_key() is None


def test_get_api_key_returns_none_when_whitespace_only(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "   ")
    assert _get_api_key() is None


def test_get_api_key_strips_whitespace(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "  fake-key-123  ")
    assert _get_api_key() == "fake-key-123"


# ---------------------------------------------------------------------------
# extract_state – offline path (no API call made)
# ---------------------------------------------------------------------------

def test_extract_state_offline_when_no_key(monkeypatch):
    """extract_state must return the OFFLINE_MODE_NOTE error and no prediction
    when GEMINI_API_KEY is absent, without attempting any network call."""
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)

    conversation = [{"role": "user", "content": "Book a table for two."}]
    system, user = build_extraction_prompt(conversation, "improved")

    parsed, raw_text, error = extract_state(
        conversation=conversation,
        mode="improved",
        system_prompt=system,
        user_prompt=user,
    )

    assert parsed is None, "Should return no prediction in offline mode"
    assert raw_text == "", "Raw text should be empty in offline mode"
    assert OFFLINE_MODE_NOTE in error, (
        f"Error message should contain the offline note, got: {error!r}"
    )


# ---------------------------------------------------------------------------
# JSON fence stripping and extraction (unit, no API)
# ---------------------------------------------------------------------------

def test_strip_json_fences_plain_json():
    raw = '{"action": "book"}'
    assert _strip_json_fences(raw) == raw


def test_strip_json_fences_with_backticks():
    raw = '```json\n{"action": "book"}\n```'
    assert _strip_json_fences(raw) == '{"action": "book"}'


def test_strip_json_fences_without_language_tag():
    raw = '```\n{"action": "book"}\n```'
    assert _strip_json_fences(raw) == '{"action": "book"}'


def test_extract_json_from_text_plain():
    assert _extract_json_from_text('{"x": 1}') == {"x": 1}


def test_extract_json_from_text_fenced():
    assert _extract_json_from_text('```json\n{"x": 1}\n```') == {"x": 1}


def test_extract_json_from_text_embedded():
    """Should find the JSON object even when surrounded by prose."""
    text = 'Here is the result:\n{"x": 1}\nEnd of output.'
    assert _extract_json_from_text(text) == {"x": 1}


def test_extract_json_from_text_returns_none_on_garbage():
    assert _extract_json_from_text("this is not json at all") is None


def test_extract_json_from_text_returns_none_on_empty():
    assert _extract_json_from_text("") is None


def test_extract_json_from_text_returns_first_of_multiple_objects():
    text = 'First: {"x": 1}\nSecond: {"x": 2}'
    assert _extract_json_from_text(text) == {"x": 1}


def test_extract_json_from_text_handles_brace_inside_string():
    text = 'Result: {"message": "use {braces} safely", "ok": true}'
    assert _extract_json_from_text(text) == {
        "message": "use {braces} safely",
        "ok": True,
    }


@pytest.mark.parametrize(
    "raw",
    ['[1, 2, 3]', '[{"nested": "object"}]', '"value"', '42', 'true'],
)
def test_extract_json_from_text_rejects_non_object_json(raw):
    assert _extract_json_from_text(raw) is None
