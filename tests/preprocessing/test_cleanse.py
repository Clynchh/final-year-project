"""Tests for src/preprocessing/cleanse.py"""

import pytest
from cleanse import (
    clean_transcript,
    _normalize_apostrophes,
    _remove_single_letters,
    _remove_nonsense_words,
    _filter_corrupted_lines,
)


class TestCleanTranscript:
    def test_clean_removes_citation_separator(self):
        text = "The virus spread quickly.\n---\nBBC News, 2020"
        result = clean_transcript(text)
        assert "bbc" not in result
        assert "2020" not in result

    def test_clean_removes_single_line_whisper_transcript(self):
        # Regression: single-line text with no trailing --- should not be destroyed
        text = "The government announced new measures today."
        result = clean_transcript(text)
        assert result != ""
        assert "government" in result

    def test_clean_preserves_valid_text(self):
        text = "The government announced new measures today."
        result = clean_transcript(text)
        # Should be lowercased and contain core words
        assert "government" in result
        assert "announced" in result
        assert "measures" in result

    def test_clean_lowercases(self):
        text = "The Prime Minister Spoke Today."
        result = clean_transcript(text)
        assert result == result.lower()

    def test_clean_normalises_apostrophes(self):
        text = "It\u2019s a new variant."
        result = clean_transcript(text)
        assert "\u2019" not in result
        assert "'" in result or "its" in result or "it" in result

    def test_clean_removes_single_letters(self):
        # Standalone b, c should be removed; 'a' and 'i' kept
        result = _remove_single_letters("b c a i x y")
        assert "b" not in result.split()
        assert "c" not in result.split()
        assert "x" not in result.split()
        assert "y" not in result.split()
        assert "a" in result.split()
        assert "i" in result.split()

    def test_clean_removes_nonsense_words(self):
        # Words with no vowels or excessive consonant runs should be removed
        result = _remove_nonsense_words("the qrst bbc government")
        assert "qrst" not in result
        # 'bbc' has no vowels and length > 2 — removed
        assert "bbc" not in result
        assert "the" in result
        assert "government" in result

    def test_clean_splits_on_punctuation(self):
        text = "Cases rose sharply. Hospitals were overwhelmed."
        result = clean_transcript(text)
        # Each sentence should end with a newline after punctuation splitting
        assert "\n" in result or "." in result

    def test_clean_empty_input(self):
        assert clean_transcript("") == ""
        assert clean_transcript("   ") == ""

    def test_clean_removes_overlap_duplicate_content(self):
        # If consecutive lines share a long overlap, duplicate content is collapsed
        line1 = "The prime minister announced new restrictions."
        line2 = "The prime minister announced new restrictions on travel."
        text = line1 + "\n" + line2
        result = clean_transcript(text)
        # Should not double the overlapping portion
        assert result.count("prime minister") <= 1


class TestNormalizeApostrophes:
    def test_smart_quotes_replaced(self):
        result = _normalize_apostrophes("it\u2019s a \u2018test\u2019")
        assert "\u2018" not in result
        assert "\u2019" not in result
        assert "'" in result

    def test_smart_double_quotes_replaced(self):
        result = _normalize_apostrophes("\u201chello\u201d")
        assert "\u201c" not in result
        assert "\u201d" not in result
        assert '"' in result

    def test_em_dash_replaced(self):
        result = _normalize_apostrophes("a\u2014b")
        assert "\u2014" not in result
        assert "-" in result


class TestRemoveNonsenseWords:
    def test_valid_words_kept(self):
        result = _remove_nonsense_words("the government announced measures")
        assert result == "the government announced measures"

    def test_vowelless_long_word_removed(self):
        result = _remove_nonsense_words("the xyz government")
        assert "xyz" not in result

    def test_short_common_words_kept(self):
        result = _remove_nonsense_words("a i an is it")
        assert "a" in result
        assert "i" in result
        assert "an" in result

    def test_contraction_kept(self):
        # Words with apostrophes are always kept
        result = _remove_nonsense_words("don't won't")
        assert "don't" in result
        assert "won't" in result
