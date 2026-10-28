"""
IntentLedger – Value normalizer.

Normalises field values so that semantically equivalent representations
compare as equal (e.g. "3pm" == "3:00 PM", "$3000" == 3000).
"""

import re


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TIME_PATTERNS = [
    # "3pm", "3 pm", "3:00pm", "3:00 PM", "15:00"
    (re.compile(r"^(\d{1,2})\s*:\s*(\d{2})\s*(am|pm)$", re.I), "hhmm_ampm"),
    (re.compile(r"^(\d{1,2})\s*(am|pm)$", re.I), "h_ampm"),
    (re.compile(r"^(\d{1,2})\s*:\s*(\d{2})$"), "hhmm_24"),
]

_MONEY_STRIP = re.compile(r"[$,\s]")


def _parse_to_minutes(value: str) -> int | None:
    """Try to parse a time-like string to minutes-since-midnight."""
    v = str(value).strip()

    # "15:00" 24h
    m = re.match(r"^(\d{1,2}):(\d{2})$", v)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        return h * 60 + mn

    # "3:00 PM"
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)$", v, re.I)
    if m:
        h, mn, meridiem = int(m.group(1)), int(m.group(2)), m.group(3).lower()
        if meridiem == "pm" and h != 12:
            h += 12
        if meridiem == "am" and h == 12:
            h = 0
        return h * 60 + mn

    # "3pm" or "3 pm"
    m = re.match(r"^(\d{1,2})\s*(am|pm)$", v, re.I)
    if m:
        h, meridiem = int(m.group(1)), m.group(2).lower()
        if meridiem == "pm" and h != 12:
            h += 12
        if meridiem == "am" and h == 12:
            h = 0
        return h * 60

    return None


def _try_numeric(value) -> float | None:
    """Try to coerce value to a float after stripping currency symbols."""
    try:
        cleaned = _MONEY_STRIP.sub("", str(value))
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def normalize(value) -> object:
    """
    Return a canonical form of *value* suitable for equality comparison.

    Order of attempts:
      1. Time string → minutes since midnight (int)
      2. Numeric / currency → float
      3. List → sorted list of normalized items
      4. String → stripped lower-case
      5. Anything else → unchanged
    """
    if isinstance(value, list):
        normalized_items = [normalize(item) for item in value]
        # Python cannot directly order unlike types (for example ``1`` and
        # ``"one"``). A deterministic type-and-representation key preserves
        # order-insensitive comparison without raising TypeError.
        return sorted(
            normalized_items,
            key=lambda item: (type(item).__name__, repr(item)),
        )

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Try time
        minutes = _parse_to_minutes(value)
        if minutes is not None:
            return minutes

        # Try numeric / currency
        numeric = _try_numeric(value)
        if numeric is not None:
            return numeric

        # Plain string
        return value.strip().lower()

    return value


def normalize_dict(d: dict) -> dict:
    """Return a new dict with all values normalized."""
    return {k: normalize(v) for k, v in d.items()}
