"""Tests for src/analysis/emotion_analysis.py.

The real transformer model is never loaded — all model calls are mocked.
"""

from unittest.mock import MagicMock
import torch
import pytest

from emotion_analysis import extract_year_month, get_emotion_batch, MONTH_MAP


class TestExtractYearMonth:
    def test_standard_filename(self):
        year, month = extract_year_month("Mar 2021.txt")
        assert year == "2021"
        assert month == "03"

    def test_january(self):
        year, month = extract_year_month("Jan 2020.txt")
        assert year == "2020"
        assert month == "01"

    def test_december(self):
        year, month = extract_year_month("Dec 2019.txt")
        assert year == "2019"
        assert month == "12"

    def test_unknown_filename(self):
        year, month = extract_year_month("unknown.txt")
        assert year is None
        assert month is None

    def test_no_year(self):
        year, month = extract_year_month("Feb.txt")
        assert year is None
        assert month == "02"

    def test_all_months_covered(self):
        for abbr, num in MONTH_MAP.items():
            _, month = extract_year_month(f"{abbr.capitalize()} 2020.txt")
            assert month == num


class TestGetEmotionBatch:
    def _make_mock_setup(self, pred_class: int, id2label: dict, batch_size: int = 1):
        n_classes = len(id2label)
        logits = torch.zeros(batch_size, n_classes)
        logits[:, pred_class] = 10.0

        mock_output = MagicMock()
        mock_output.logits = logits

        mock_model = MagicMock(return_value=mock_output)
        mock_tokenizer = MagicMock(return_value={
            "input_ids": torch.zeros(batch_size, 5, dtype=torch.long),
            "attention_mask": torch.ones(batch_size, 5, dtype=torch.long),
        })
        device = torch.device("cpu")
        return mock_tokenizer, mock_model, device

    def test_emotion_label_from_id2label(self):
        id2label = {0: "anger", 1: "disgust", 2: "fear", 3: "joy",
                    4: "neutral", 5: "sadness", 6: "surprise"}
        tokenizer, model, device = self._make_mock_setup(pred_class=3, id2label=id2label)
        results = get_emotion_batch(["happy news today"], tokenizer, model, device, id2label)
        emotion, confidence = results[0]
        assert emotion == "joy"

    def test_batch_returns_correct_length(self):
        id2label = {0: "anger", 1: "disgust", 2: "fear", 3: "joy",
                    4: "neutral", 5: "sadness", 6: "surprise"}
        tokenizer, model, device = self._make_mock_setup(pred_class=0, id2label=id2label, batch_size=5)
        texts = ["text one", "text two", "text three", "text four", "text five"]
        results = get_emotion_batch(texts, tokenizer, model, device, id2label)
        assert len(results) == 5

    def test_confidence_is_float_in_range(self):
        id2label = {0: "fear", 1: "joy"}
        tokenizer, model, device = self._make_mock_setup(pred_class=0, id2label=id2label)
        results = get_emotion_batch(["scary news"], tokenizer, model, device, id2label)
        emotion, confidence = results[0]
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_result_tuple_structure(self):
        id2label = {0: "neutral"}
        tokenizer, model, device = self._make_mock_setup(pred_class=0, id2label=id2label)
        results = get_emotion_batch(["test"], tokenizer, model, device, id2label)
        assert len(results[0]) == 2  # (emotion, confidence)

    def test_anger_class_0_by_default(self):
        id2label = {0: "anger", 1: "disgust", 2: "fear", 3: "joy",
                    4: "neutral", 5: "sadness", 6: "surprise"}
        tokenizer, model, device = self._make_mock_setup(pred_class=0, id2label=id2label)
        results = get_emotion_batch(["rage"], tokenizer, model, device, id2label)
        emotion, _ = results[0]
        assert emotion == "anger"
