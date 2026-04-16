"""Tests for src/preprocessing/filter_relevant_tight.py — is_covid_relevant()."""

import pytest
from filter_relevant_tight import is_covid_relevant


class TestIsCovidRelevant:
    # --- Direct terms (one match = True) ---

    def test_direct_term_covid(self):
        assert is_covid_relevant("The covid situation is serious.") is True

    def test_direct_term_coronavirus(self):
        assert is_covid_relevant("Coronavirus cases have increased.") is True

    def test_direct_term_covid19(self):
        assert is_covid_relevant("The covid-19 pandemic changed everything.") is True

    def test_direct_term_sars_cov_2(self):
        assert is_covid_relevant("The sars-cov-2 virus was identified in 2019.") is True

    def test_direct_term_case_insensitive(self):
        assert is_covid_relevant("COVID is spreading rapidly.") is True
        assert is_covid_relevant("Covid cases rose sharply.") is True

    # --- Indirect terms (need 2+ matches) ---

    def test_two_indirect_terms_match(self):
        assert is_covid_relevant("The lockdown measures during the pandemic were strict.") is True

    def test_one_indirect_term_no_match(self):
        assert is_covid_relevant("The lockdown affected businesses.") is False

    def test_no_terms_no_match(self):
        assert is_covid_relevant("The weather was sunny yesterday.") is False

    def test_mixed_direct_and_indirect(self):
        # One direct term alone is sufficient
        assert is_covid_relevant("The virus spread through the hospital.") is True

    def test_empty_string(self):
        assert is_covid_relevant("") is False

    def test_two_different_indirect_terms(self):
        assert is_covid_relevant("The pandemic led to widespread quarantine orders.") is True

    def test_same_indirect_term_twice(self):
        # The regex findall should count both occurrences
        assert is_covid_relevant("The hospital treated many patients in hospital.") is True

    def test_word_boundary_respected_for_direct_term(self):
        # "epicovid" should not match "covid" at a word boundary
        assert is_covid_relevant("The epicovid study was interesting.") is False
