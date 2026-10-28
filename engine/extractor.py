"""
IntentLedger – Model extractor.

Calls the Google Gen AI SDK to extract a JSON state from a conversation.
Falls back gracefully when the model is unavailable or JSON is invalid.
"""

from __future__ import annotations

import json
import os
import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "gemma-4-26b-a4b-it"
MODEL_ENV_VAR = "INTENTLEDGER_MODEL"
API_KEY_ENV_VAR = "GEMINI_API_KEY"

OFFLINE_MODE_NOTE = (
    "OFFLINE MODE – no model call was made. "
    "Set the GEMINI_API_KEY environment variable to enable live evaluation."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_model_name() -> str:
    configured = os.environ.get(MODEL_ENV_VAR, "").strip()
    return configured or DEFAULT_MODEL


def _get_api_key() -> str | None:
    key = os.environ.get(API_KEY_ENV_VAR, "")
    return key.strip() if key.strip() else None


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences that wrap JSON."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_from_text(text: str) -> dict | None:
    """Try to parse the first JSON object in *text*, including after stripping fences.

    Valid JSON arrays and scalar values are intentionally rejected because the
    scoring pipeline requires a mapping of field names to values.
    """
    candidates = [text, _strip_json_fences(text)]
    for c in candidates:
        try:
            parsed = json.loads(c)
            if isinstance(parsed, dict):
                return parsed
            # The complete response is valid JSON but has the wrong top-level
            # shape. Do not mine a nested object from an array or scalar.
            return None
        except json.JSONDecodeError:
            pass

    # Last resort: scan for the first decodable object. A greedy ``{.*}``
    # expression incorrectly joins multiple objects and fails on braces inside
    # quoted strings, while JSONDecoder handles both cases correctly.
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            parsed, _ = decoder.raw_decode(text[match.start():])
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            continue

    return None


# ---------------------------------------------------------------------------
# Public extraction function
# ---------------------------------------------------------------------------

def extract_state(
    conversation: list[dict],
    mode: str,
    system_prompt: str,
    user_prompt: str,
) -> tuple[dict | None, str, str]:
    """
    Call the model and return the extracted state.

    Args:
        conversation: list of {role, content} turns (for context; prompts are pre-built)
        mode: 'baseline' or 'improved'
        system_prompt: system instruction string
        user_prompt: user turn string containing the transcript

    Returns:
        (parsed_dict | None, raw_text, error_message)
        parsed_dict is None when extraction failed.
        error_message is empty on success.
    """
    api_key = _get_api_key()

    # ---- Offline mode ----
    if not api_key:
        return None, "", OFFLINE_MODE_NOTE

    model_name = _get_model_name()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0,
                max_output_tokens=1024,
            ),
        )

        raw_text = response.text or ""

    except ImportError:
        return None, "", (
            "google-genai package not installed. "
            "Run: pip install google-genai"
        )
    except Exception as exc:  # noqa: BLE001
        err = str(exc)
        # Classify common errors
        if "quota" in err.lower() or "429" in err:
            err = f"API quota exceeded: {err}"
        elif "invalid" in err.lower() and "key" in err.lower():
            err = f"Invalid API key: {err}"
        elif "not found" in err.lower() or "404" in err:
            err = f"Model not found ({model_name}): {err}"
        else:
            err = f"Model call failed: {err}"
        return None, "", err

    # ---- Parse JSON ----
    parsed = _extract_json_from_text(raw_text)
    if parsed is None:
        return None, raw_text, (
            f"Model returned non-JSON output:\n{raw_text[:500]}"
        )

    return parsed, raw_text, ""


# ---------------------------------------------------------------------------
# Supported model check (lightweight)
# ---------------------------------------------------------------------------

def check_model_supported(model_name: str | None = None) -> tuple[bool, str]:
    """
    Verify the configured model is accessible.

    Returns (ok, message).
    """
    api_key = _get_api_key()
    if not api_key:
        return False, "No API key set (GEMINI_API_KEY). Running in offline mode."

    name = model_name or _get_model_name()
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        # This does a lightweight list-models call
        models = [m.name for m in client.models.list()]
        # model names come back as "models/gemma-4-26b-a4b-it" etc.
        matched = any(name in m for m in models)
        if matched:
            return True, f"Model '{name}' is available."
        else:
            available = ", ".join(m.split("/")[-1] for m in models[:8])
            return False, (
                f"Model '{name}' not found. Available: {available} …"
            )
    except Exception as exc:  # noqa: BLE001
        return False, f"Could not verify model: {exc}"
