import os
import spacy  # type: ignore
from pathlib import Path

CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in CURRENT.parents if (p / "Data").exists())

CLEAN_BASE = PROJECT_ROOT / "Data" / "clean" / "BBC News TV"
SEGMENTED_BASE = PROJECT_ROOT / "Data" / "segmented" / "BBC News TV"

nlp = spacy.load(
    "en_core_web_sm",
    disable=["ner", "tagger", "lemmatizer"]
)

def segment_text(text: str) -> list[str]:
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

for root, _, files in os.walk(CLEAN_BASE):
    root_path = Path(root)

    if not files:
        continue

    rel_path = root_path.relative_to(CLEAN_BASE)
    output_dir = SEGMENTED_BASE / rel_path
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename in files:
        if not filename.lower().endswith(".txt"):
            continue

        input_file = root_path / filename
        output_file = output_dir / filename

        with open(input_file, "r", encoding="utf-8") as f:
            text = f.read()

        sentences = segment_text(text)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(sentences))
