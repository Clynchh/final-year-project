# Applies the tight COVID filter to data/sampled/ → data/filtered/sample/.
# Run after sample_sentences.py so the random sample only contains COVID-relevant sentences.

from pathlib import Path
from filter_relevant_tight import is_covid_relevant

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

SAMPLED_DIR = PROJECT_ROOT / "data" / "sampled"
FILTERED_DIR = PROJECT_ROOT / "data" / "filtered" / "sample"

if __name__ == "__main__":
    for input_path in sorted(SAMPLED_DIR.rglob("*.txt")):
        rel_dir = input_path.parent.relative_to(SAMPLED_DIR)
        output_dir = FILTERED_DIR / rel_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        sentences = input_path.read_text(encoding="utf-8").splitlines()
        relevant = [sentence.strip() for sentence in sentences if sentence.strip() and is_covid_relevant(sentence)]

        if not relevant:
            continue

        output_path = output_dir / input_path.name
        output_path.write_text("\n".join(relevant) + "\n", encoding="utf-8")
        print(f"Filtered (sample): {input_path.name} {len(sentences)} -> {len(relevant)} sentences")
