"""Tests for src/analysis/polarity_analysis.py.

The real transformer model is never loaded — all model calls are mocked.
"""

import csv
from pathlib import Path
from unittest.mock import MagicMock, patch
import torch
import pytest

from polarity_analysis import (
    extract_year_month_from_filename,
    get_sentiment_batch,
    LABEL_MAP,
    SCORE_MAP,
    MONTH_MAP,
)


class TestExtractYearMonthFromFilename:
    def test_standard_filename(self):
        year, month = extract_year_month_from_filename("Jan 2020.txt")
        assert year == "2020"
        assert month == "01"

    def test_different_month(self):
        year, month = extract_year_month_from_filename("Mar 2021.txt")
        assert year == "2021"
        assert month == "03"

    def test_december(self):
        year, month = extract_year_month_from_filename("Dec 2019.txt")
        assert year == "2019"
        assert month == "12"

    def test_unknown_month(self):
        year, month = extract_year_month_from_filename("unknown_file.txt")
        assert year is None
        assert month is None

    def test_no_year(self):
        year, month = extract_year_month_from_filename("Jan.txt")
        assert year is None
        assert month == "01"

    def test_all_months_in_map(self):
        for abbr, num in MONTH_MAP.items():
            year, month = extract_year_month_from_filename(f"{abbr.capitalize()} 2020.txt")
            assert month == num


class TestLabelMap:
    def test_label_map_keys(self):
        assert 0 in LABEL_MAP
        assert 1 in LABEL_MAP

    def test_label_map_values(self):
        assert LABEL_MAP[0] == "negative"
        assert LABEL_MAP[1] == "positive"

    def test_score_map_negative(self):
        assert SCORE_MAP["negative"] == -1

    def test_score_map_positive(self):
        assert SCORE_MAP["positive"] == 1

    def test_score_map_neutral(self):
        assert SCORE_MAP["neutral"] == 0


class TestGetSentimentBatch:
    def _make_mock_model_output(self, pred_class: int, batch_size: int = 1):
        """Return a mock model and tokenizer that predict pred_class for all inputs."""
        # logits: shape [batch_size, 2]; pred_class gets high logit
        logits = torch.zeros(batch_size, 2)
        logits[:, pred_class] = 10.0  # high confidence for pred_class

        mock_output = MagicMock()
        mock_output.logits = logits

        mock_model = MagicMock(return_value=mock_output)
        mock_tokenizer = MagicMock(return_value={
            "input_ids": torch.zeros(batch_size, 5, dtype=torch.long),
            "attention_mask": torch.ones(batch_size, 5, dtype=torch.long),
        })
        device = torch.device("cpu")
        return mock_tokenizer, mock_model, device

    def test_returns_negative_for_class_0(self):
        tokenizer, model, device = self._make_mock_model_output(pred_class=0)
        results = get_sentiment_batch(["bad news today"], tokenizer, model, device)
        assert len(results) == 1
        label, score, confidence = results[0]
        assert label == "negative"
        assert score == -1

    def test_returns_positive_for_class_1(self):
        tokenizer, model, device = self._make_mock_model_output(pred_class=1)
        results = get_sentiment_batch(["great news today"], tokenizer, model, device)
        label, score, confidence = results[0]
        assert label == "positive"
        assert score == 1

    def test_batch_returns_correct_length(self):
        tokenizer, model, device = self._make_mock_model_output(pred_class=1, batch_size=3)
        texts = ["text one", "text two", "text three"]
        results = get_sentiment_batch(texts, tokenizer, model, device)
        assert len(results) == 3

    def test_confidence_is_float_in_range(self):
        tokenizer, model, device = self._make_mock_model_output(pred_class=1)
        results = get_sentiment_batch(["sample text"], tokenizer, model, device)
        _, _, confidence = results[0]
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_result_tuple_structure(self):
        tokenizer, model, device = self._make_mock_model_output(pred_class=0)
        results = get_sentiment_batch(["test"], tokenizer, model, device)
        assert len(results[0]) == 3  # (label, score, confidence)
