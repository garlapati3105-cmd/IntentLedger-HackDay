"""
Tests for engine.normalizer – value normalisation rules.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from engine.normalizer import normalize, normalize_dict


# ---------------------------------------------------------------------------
# Time strings
# ---------------------------------------------------------------------------

class TestTimeNormalization:
    def test_3pm(self):
        assert normalize("3pm") == normalize("3:00 PM")

    def test_3pm_lowercase(self):
        assert normalize("3pm") == normalize("3:00 pm")

    def test_15_00_24h(self):
        assert normalize("15:00") == normalize("3:00 PM")

    def test_12pm_noon(self):
        assert normalize("12pm") == normalize("12:00 PM")

    def test_12am_midnight(self):
        assert normalize("12am") == normalize("0:00")

    def test_9am(self):
        assert normalize("9am") == normalize("9:00 AM")

    def test_different_times_not_equal(self):
        assert normalize("2pm") != normalize("3pm")


# ---------------------------------------------------------------------------
# Numeric / Currency
# ---------------------------------------------------------------------------

class TestNumericNormalization:
    def test_dollar_sign(self):
        assert normalize("$3000") == normalize(3000)

    def test_dollar_comma(self):
        assert normalize("$3,000") == normalize(3000)

    def test_int_float(self):
        assert normalize(4) == normalize(4.0)

    def test_party_size(self):
        assert normalize("4") == normalize(4)


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------

class TestListNormalization:
    def test_list_sorted(self):
        assert normalize(["Carol", "Alice", "Bob"]) == normalize(["Alice", "Bob", "Carol"])

    def test_single_item_list(self):
        assert normalize(["alice"]) == normalize(["Alice"])

    def test_mixed_type_list_is_order_insensitive(self):
        assert normalize(["Alice", 2, True]) == normalize([True, "alice", 2.0])


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------

class TestStringNormalization:
    def test_case_insensitive(self):
        assert normalize("Bella Italia") == normalize("bella italia")

    def test_strip_whitespace(self):
        assert normalize("  Kyoto  ") == normalize("Kyoto")

    def test_ambiguous_preserved(self):
        assert normalize("AMBIGUOUS") == "ambiguous"


# ---------------------------------------------------------------------------
# normalize_dict
# ---------------------------------------------------------------------------

class TestNormalizeDict:
    def test_normalizes_all_values(self):
        result = normalize_dict({"time": "3pm", "budget": "$2,000", "name": "Alice"})
        assert result["time"] == normalize("3:00 PM")
        assert result["budget"] == 2000.0
        assert result["name"] == "alice"
