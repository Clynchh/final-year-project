import re
from pathlib import Path

from constants import COVID_TERMS

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

SEGMENTED_DIR = PROJECT_ROOT / "data" / "segmented"
FILTERED_DIR = PROJECT_ROOT / "data" / "filtered" / "loose"

COVID_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in COVID_TERMS) + r")\b",
    re.IGNORECASE,
)

if __name__ == "__main__":
    for input_path in sorted(SEGMENTED_DIR.rglob("*.txt")):
        rel_dir = input_path.parent.relative_to(SEGMENTED_DIR)
        output_dir = FILTERED_DIR / rel_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        sentences = input_path.read_text(encoding="utf-8").splitlines()
        relevant = [s.strip() for s in sentences if COVID_REGEX.search(s)]

        if not relevant:
            continue

        output_path = output_dir / input_path.name
        output_path.write_text("\n".join(relevant) + "\n", encoding="utf-8")
        print(f"Filtered (loose): {input_path} -> {output_path}")
