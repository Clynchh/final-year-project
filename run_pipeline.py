# Orchestrates the full pipeline: cleanse → segment → filter → sample → filter_sample → sentiment → summary → convert.
# Supports resuming from a named step via --from <step>.
# Use --model vader to run VADER instead of RoBERTa for the sentiment step.

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC = PROJECT_ROOT / "src"

STEPS = [
    ("cleanse",   SRC / "preprocessing" / "cleanse.py"),
    ("segment",   SRC / "preprocessing" / "segment.py"),
    ("filter",    [
        SRC / "preprocessing" / "filter_relevant_loose.py",
        SRC / "preprocessing" / "filter_relevant_tight.py",
    ]),
    ("sample",        SRC / "preprocessing" / "sample_sentences.py"),
    ("filter_sample", SRC / "preprocessing" / "filter_sample.py"),
    ("sentiment",     None),  # resolved at runtime based on --model
    ("emotion",   SRC / "analysis" / "emotion_analysis.py"),
    ("summary",   SRC / "analysis" / "summary.py"),
    ("convert",   [
        SRC / "analysis" / "csv_to_json.py",
        SRC / "analysis" / "generate_sentence_count.py",
        SRC / "analysis" / "sentence_count_to_json.py",
        SRC / "analysis" / "emotion_to_json.py",
    ]),
]


def run_script(script: Path, extra_args: list[str] = []) -> None:
    print(f"\n{'='*60}\nRunning: {script.relative_to(PROJECT_ROOT)}\n{'='*60}")
    result = subprocess.run([sys.executable, str(script)] + extra_args, check=False)
    if result.returncode != 0:
        print(f"\nERROR: {script.name} exited with code {result.returncode}. Aborting.")
        sys.exit(result.returncode)


def main() -> None:
    start_from = None
    if "--from" in sys.argv:
        idx = sys.argv.index("--from")
        if idx + 1 < len(sys.argv):
            start_from = sys.argv[idx + 1]

    filter_type = "tight"
    if "--filter" in sys.argv:
        idx = sys.argv.index("--filter")
        if idx + 1 < len(sys.argv):
            filter_type = sys.argv[idx + 1]

    model = "altmodel"
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]

    # resolve sentiment script based on model
    sentiment_script = (
        SRC / "analysis" / "vader_analysis.py"
        if model == "vader"
        else SRC / "analysis" / "polarity_analysis.py"
    )

    filter_arg = ["--filter", filter_type]
    model_arg  = ["--model", model]
    filter_steps = {"sentiment", "emotion", "summary", "convert"}
    model_steps  = {"summary", "convert"}  # steps that also accept --model

    step_names = [name for name, _ in STEPS]
    if start_from and start_from not in step_names:
        print(f"Unknown step '{start_from}'. Valid steps: {', '.join(step_names)}")
        sys.exit(1)

    print(f"Filter: {filter_type} | Model: {model}")
    active = start_from is None
    for name, scripts in STEPS:
        if start_from == name:
            active = True
        if not active:
            print(f"Skipping: {name}")
            continue

        # resolve sentiment script
        if name == "sentiment":
            scripts = sentiment_script

        script_list = scripts if isinstance(scripts, list) else [scripts]

        for script in script_list:
            if "sentence_count_to_json" in script.name or "generate_sentence_count" in script.name:
                run_script(script, [])
            elif name == "emotion" or "emotion_to_json" in script.name:
                # emotion steps only run for altmodel, not vader
                if model == "altmodel":
                    run_script(script, filter_arg)
            else:
                args = []
                if name in filter_steps:
                    args += filter_arg
                if name in model_steps:
                    args += model_arg
                run_script(script, args)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
