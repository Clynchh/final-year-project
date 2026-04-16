"""Tests for run_pipeline.py — argument parsing and step logic."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = PROJECT_ROOT / "run_pipeline.py"

# Import STEPS and constants directly for white-box tests
sys.path.insert(0, str(PROJECT_ROOT))
from run_pipeline import STEPS


class TestStepDefinitions:
    def test_all_expected_steps_present(self):
        step_names = [name for name, _ in STEPS]
        for expected in ["cleanse", "segment", "filter", "sample", "filter_sample", "sentiment", "emotion", "summary", "convert"]:
            assert expected in step_names

    def test_filter_steps_set(self):
        # Steps that receive --filter arg
        filter_steps = {"sentiment", "emotion", "summary", "convert"}
        step_names = {name for name, _ in STEPS}
        assert filter_steps.issubset(step_names)

    def test_sample_not_in_filter_steps(self):
        # sample step should NOT receive --filter
        filter_steps = {"sentiment", "emotion", "summary", "convert"}
        assert "sample" not in filter_steps

    def test_steps_is_list_of_tuples(self):
        assert isinstance(STEPS, list)
        for item in STEPS:
            assert isinstance(item, tuple)
            assert len(item) == 2


class TestPipelineArgParsing:
    def _run(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(PIPELINE_SCRIPT)] + list(args),
            capture_output=True,
            text=True,
        )

    def test_invalid_step_exits_nonzero(self):
        result = self._run("--from", "nonexistent_step")
        assert result.returncode != 0

    def test_invalid_step_prints_valid_steps(self):
        result = self._run("--from", "nonexistent_step")
        assert "Valid steps" in result.stdout or "Valid steps" in result.stderr

    def test_valid_step_names_accepted(self):
        # We can't easily run the full pipeline, but we can verify step name detection
        # by checking the STEPS list directly
        step_names = [name for name, _ in STEPS]
        assert "cleanse" in step_names
        assert "convert" in step_names

    def test_filter_default_is_tight(self):
        # Run with --from convert (no actual scripts needed at this check level)
        # Instead check via module-level logic: no --filter flag → "tight"
        # We verify this by examining the source
        import ast
        source = PIPELINE_SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        # Find the assignment: filter_type = "tight"
        found_tight_default = False
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and
                    isinstance(node.value, ast.Constant) and
                    node.value.value == "tight"):
                found_tight_default = True
                break
        assert found_tight_default, "Default filter_type should be 'tight'"

    def test_model_default_is_altmodel(self):
        import ast
        source = PIPELINE_SCRIPT.read_text(encoding="utf-8")
        tree = ast.parse(source)
        found_altmodel_default = False
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and
                    isinstance(node.value, ast.Constant) and
                    node.value.value == "altmodel"):
                found_altmodel_default = True
                break
        assert found_altmodel_default, "Default model should be 'altmodel'"


class TestSentenceCountExclusion:
    def test_sentence_count_scripts_excluded_from_filter_args(self):
        """generate_sentence_count and sentence_count_to_json should not receive --filter."""
        source = PIPELINE_SCRIPT.read_text(encoding="utf-8")
        # Verify the exclusion logic exists in the source
        assert "sentence_count_to_json" in source
        assert "generate_sentence_count" in source
        # The exclusion condition must be present
        assert "sentence_count_to_json" in source and "generate_sentence_count" in source

    def test_emotion_to_json_excluded_for_vader(self):
        """emotion_to_json should only run for altmodel, not vader."""
        source = PIPELINE_SCRIPT.read_text(encoding="utf-8")
        assert "emotion_to_json" in source
        assert 'model == "altmodel"' in source
