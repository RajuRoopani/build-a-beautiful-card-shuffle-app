"""
test_string_utils.py — Unit tests for the string utilities module.

Run with:
    python -m pytest tests/test_string_utils.py -v
"""

import pytest
from src.string_utils.string_utils import truncate, slugify, count_words, title_case


# ---------------------------------------------------------------------------
# truncate
# ---------------------------------------------------------------------------

class TestTruncate:
    def test_no_truncation_needed(self) -> None:
        """Text shorter than max_len returns unchanged."""
        assert truncate("Hello", 10) == "Hello"

    def test_truncation_with_default_suffix(self) -> None:
        """Truncation with default suffix '...' fits exactly to max_len."""
        assert truncate("Hello World", 8) == "Hello..."

    def test_truncation_with_custom_suffix(self) -> None:
        """Truncation with custom suffix fits exactly to max_len."""
        assert truncate("Hello World", 7, suffix="..") == "Hello.."

    def test_edge_case_max_len_less_than_suffix_length(self) -> None:
        """When max_len <= len(suffix), suffix is truncated to max_len."""
        assert truncate("Hello", 2) == ".."

    def test_empty_string_input(self) -> None:
        """Empty string input returns empty string."""
        assert truncate("", 10) == ""


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic_text(self) -> None:
        """Basic text with spaces is converted to lowercase with hyphens."""
        assert slugify("Hello World") == "hello-world"

    def test_special_characters(self) -> None:
        """Special characters are removed, spaces and special chars become hyphens."""
        assert slugify("Hello World! Foo & Bar") == "hello-world-foo-bar"

    def test_consecutive_spaces_and_hyphens(self) -> None:
        """Multiple consecutive spaces/hyphens collapse to single hyphen."""
        assert slugify("foo   bar--baz") == "foo-bar-baz"

    def test_underscores_converted_to_hyphens(self) -> None:
        """Underscores are replaced with hyphens."""
        assert slugify("foo_bar_baz") == "foo-bar-baz"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert slugify("") == ""


# ---------------------------------------------------------------------------
# count_words
# ---------------------------------------------------------------------------

class TestCountWords:
    def test_normal_sentence(self) -> None:
        """Normal sentence with two words."""
        assert count_words("hello world") == 2

    def test_empty_string(self) -> None:
        """Empty string contains zero words."""
        assert count_words("") == 0

    def test_whitespace_only(self) -> None:
        """String with only whitespace contains zero words."""
        assert count_words("   ") == 0

    def test_extra_whitespace_between_words(self) -> None:
        """Extra whitespace between and around words is handled correctly."""
        assert count_words("  hello   world  ") == 2

    def test_multiple_words(self) -> None:
        """Count multiple words correctly."""
        assert count_words("the quick brown fox") == 4


# ---------------------------------------------------------------------------
# title_case
# ---------------------------------------------------------------------------

class TestTitleCase:
    def test_normal_sentence(self) -> None:
        """Normal sentence with small words capitalized appropriately."""
        assert title_case("the lord of the rings") == "The Lord of the Rings"

    def test_sentence_starting_with_preposition(self) -> None:
        """First word is capitalized even if it's a preposition."""
        assert title_case("a tale of two cities") == "A Tale of Two Cities"

    def test_single_word(self) -> None:
        """Single word is capitalized."""
        assert title_case("hello") == "Hello"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert title_case("") == ""

    def test_all_preposition_sentence(self) -> None:
        """First word capitalized, rest stay lowercase as they're small words."""
        assert title_case("a of the in on") == "A of the in on"
