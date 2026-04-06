# Proportionally samples sentences from data/segmented/ into data/sampled/.
# Sample rate calibrated so total sentences ~= loose filter count (~13,500).

import random
from pathlib import Path

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

SEGMENTED_DIR = PROJECT_ROOT / "data" / "segmented"
SAMPLED_DIR = PROJECT_ROOT / "data" / "sampled"

SAMPLE_RATE = 0.029  # ~2.9% per file → ~13,500 sentences total across all 466 files

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)

    total = 0
    for input_path in sorted(SEGMENTED_DIR.rglob("*.txt")):
        sentences = [s.strip() for s in input_path.read_text(encoding="utf-8").splitlines() if s.strip()]

        n_sample = max(1, round(len(sentences) * SAMPLE_RATE))
        sampled = random.sample(sentences, min(n_sample, len(sentences)))

        rel_dir = input_path.parent.relative_to(SEGMENTED_DIR)
        output_dir = SAMPLED_DIR / rel_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / input_path.name
        output_path.write_text("\n".join(sampled) + "\n", encoding="utf-8")

        total += len(sampled)
        print(f"Sampled {len(sampled)}/{len(sentences)} sentences: {input_path.name}")

    print(f"\nTotal sentences sampled: {total}")
