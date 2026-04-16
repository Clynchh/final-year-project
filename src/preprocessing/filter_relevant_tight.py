import re
from pathlib import Path

from constants import DIRECT_TERMS, INDIRECT_TERMS

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

SEGMENTED_DIR = PROJECT_ROOT / "data" / "segmented"
FILTERED_DIR = PROJECT_ROOT / "data" / "filtered" / "tight"

DIRECT_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in DIRECT_TERMS) + r")\b",
    re.IGNORECASE,
)
INDIRECT_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in INDIRECT_TERMS) + r")\b",
    re.IGNORECASE,
)


def is_covid_relevant(sentence: str) -> bool:
    if DIRECT_REGEX.search(sentence):
        return True
    return len(INDIRECT_REGEX.findall(sentence)) >= 2


if __name__ == "__main__":
    for input_path in sorted(SEGMENTED_DIR.rglob("*.txt")):
        rel_dir = input_path.parent.relative_to(SEGMENTED_DIR)
        output_dir = FILTERED_DIR / rel_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        sentences = input_path.read_text(encoding="utf-8").splitlines()
        relevant = [sentence.strip() for sentence in sentences if is_covid_relevant(sentence)]

        if not relevant:
            continue

        output_path = output_dir / input_path.name
        output_path.write_text("\n".join(relevant) + "\n", encoding="utf-8")
        print(f"Filtered (tight): {input_path} -> {output_path}")
