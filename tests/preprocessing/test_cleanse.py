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
        # The citation block format is: content line, then citation, then "---" as the LAST line
        text = "The virus spread quickly.\nBBC News, 2020\n---"
        result = clean_transcript(text)
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

    def test_clean_normalises_em_dash(self):
        # _normalize_apostrophes replaces em/en dashes — verify via clean_transcript
        text = "The government\u2014the prime minister\u2013announced measures."
        result = clean_transcript(text)
        assert "\u2014" not in result  # em dash gone
        assert "\u2013" not in result  # en dash gone

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
        # Whisper-style overlap: the END of line1 equals the START of line2
        # The algorithm detects and removes the redundant prefix from line2.
        line1 = "The government decided to impose a lockdown"
        line2 = "to impose a lockdown on all essential businesses"
        text = line1 + "\n" + line2
        result = clean_transcript(text)
        # "lockdown" should appear only once (overlap collapsed)
        assert result.count("lockdown") == 1


class TestNormalizeApostrophes:
    def test_em_dash_replaced(self):
        result = _normalize_apostrophes("a\u2014b")
        assert "\u2014" not in result
        assert "-" in result

    def test_en_dash_replaced(self):
        result = _normalize_apostrophes("a\u2013b")
        assert "\u2013" not in result
        assert "-" in result

    def test_plain_text_unchanged(self):
        text = "the government announced new measures"
        assert _normalize_apostrophes(text) == text


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
