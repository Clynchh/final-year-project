"""Tests for src/preprocessing/segment.py — segment_text()."""

from unittest.mock import MagicMock
import pytest
import segment as seg


def _make_mock_nlp(sentences: list[str]):
    """Return a mock nlp callable that yields fake spaCy sentences."""
    mock_sent_objects = []
    for s in sentences:
        sent = MagicMock()
        sent.text = s
        mock_sent_objects.append(sent)

    mock_doc = MagicMock()
    mock_doc.sents = iter(mock_sent_objects)

    mock_nlp = MagicMock(return_value=mock_doc)
    return mock_nlp


class TestSegmentText:
    def setup_method(self):
        # Reset nlp before each test
        seg.nlp = None

    def test_segment_splits_simple_sentences(self):
        seg.nlp = _make_mock_nlp(["Hello.", "World."])
        result = seg.segment_text("Hello. World.")
        assert result == ["Hello.", "World."]

    def test_segment_handles_empty_string(self):
        # spaCy returns no sents for empty string — mock accordingly
        mock_doc = MagicMock()
        mock_doc.sents = iter([])
        seg.nlp = MagicMock(return_value=mock_doc)
        result = seg.segment_text("")
        assert result == []

    def test_segment_strips_whitespace(self):
        seg.nlp = _make_mock_nlp(["  Hello.  ", "  World.  "])
        result = seg.segment_text("  Hello.   World.  ")
        assert result == ["Hello.", "World."]

    def test_segment_single_sentence(self):
        seg.nlp = _make_mock_nlp(["The government announced new measures."])
        result = seg.segment_text("The government announced new measures.")
        assert len(result) == 1
        assert result[0] == "The government announced new measures."

    def test_segment_excludes_blank_sentences(self):
        # Blank-text sents (whitespace only) must be filtered out
        seg.nlp = _make_mock_nlp(["Real sentence.", "   ", "Another one."])
        result = seg.segment_text("Real sentence. Another one.")
        assert "   " not in result
        assert len(result) == 2

    def test_segment_returns_list(self):
        seg.nlp = _make_mock_nlp(["One sentence."])
        result = seg.segment_text("One sentence.")
        assert isinstance(result, list)
