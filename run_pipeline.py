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
    ("sentiment", SRC / "analysis" / "sentiment.py"),
    ("summary",   SRC / "analysis" / "summary.py"),
    ("convert",   [
        SRC / "analysis" / "csv_to_json.py",
        SRC / "analysis" / "count_csv_to_json.py",
    ]),
]


def run_script(script: Path) -> None:
    print(f"\n{'='*60}\nRunning: {script.relative_to(PROJECT_ROOT)}\n{'='*60}")
    result = subprocess.run([sys.executable, str(script)], check=False)
    if result.returncode != 0:
        print(f"\nERROR: {script.name} exited with code {result.returncode}. Aborting.")
        sys.exit(result.returncode)


def main() -> None:
    start_from = None  # set via --from <step> to skip earlier steps
    if "--from" in sys.argv:
        idx = sys.argv.index("--from")
        if idx + 1 < len(sys.argv):
            start_from = sys.argv[idx + 1]

    step_names = [name for name, _ in STEPS]
    if start_from and start_from not in step_names:
        print(f"Unknown step '{start_from}'. Valid steps: {', '.join(step_names)}")
        sys.exit(1)

    active = start_from is None
    for name, scripts in STEPS:
        if start_from == name:
            active = True
        if not active:
            print(f"Skipping: {name}")
            continue

        script_list = scripts if isinstance(scripts, list) else [scripts]
        for script in script_list:
            run_script(script)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
