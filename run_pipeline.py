# Orchestrates the full pipeline: cleanse → segment → filter → sentiment → summary → convert.
# Supports resuming from a named step via --from <step>.

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
    ("sample",    SRC / "preprocessing" / "sample_sentences.py"),
    ("sentiment", SRC / "analysis" / "polarity_analysis.py"),
    ("emotion",   SRC / "analysis" / "emotion_analysis.py"),
    ("summary",   SRC / "analysis" / "summary.py"),
    ("convert",   [
        SRC / "analysis" / "csv_to_json.py",
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
    start_from = None  # set via --from <step> to skip earlier steps
    if "--from" in sys.argv:
        idx = sys.argv.index("--from")
        if idx + 1 < len(sys.argv):
            start_from = sys.argv[idx + 1]

    filter_type = "tight"  # set via --filter tight|loose|sample
    if "--filter" in sys.argv:
        idx = sys.argv.index("--filter")
        if idx + 1 < len(sys.argv):
            filter_type = sys.argv[idx + 1]

    filter_arg = ["--filter", filter_type]
    filter_steps = {"sentiment", "emotion", "summary", "convert"}  # steps that accept --filter (sample does not)

    step_names = [name for name, _ in STEPS]
    if start_from and start_from not in step_names:
        print(f"Unknown step '{start_from}'. Valid steps: {', '.join(step_names)}")
        sys.exit(1)

    print(f"Filter: {filter_type}")
    active = start_from is None
    for name, scripts in STEPS:
        if start_from == name:
            active = True
        if not active:
            print(f"Skipping: {name}")
            continue

        script_list = scripts if isinstance(scripts, list) else [scripts]
        args = filter_arg if name in filter_steps else []
        for script in script_list:
            # count_csv_to_json.py doesn't need --filter
            run_script(script, args if "sentence_count_to_json" not in script.name else [])

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
