import spacy  # type: ignore
from pathlib import Path

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

CLEAN_BASE = PROJECT_ROOT / "data" / "clean"
SEGMENTED_BASE = PROJECT_ROOT / "data" / "segmented"


def segment_text(text: str) -> list[str]:
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


if __name__ == "__main__":
    nlp = spacy.load("en_core_web_sm", disable=["ner", "tagger", "lemmatizer"])

    for root_path in sorted(CLEAN_BASE.rglob("*")):
        if not root_path.is_dir():
            continue

        txt_files = sorted(root_path.glob("*.txt"))
        if not txt_files:
            continue

        rel_path = root_path.relative_to(CLEAN_BASE)
        output_dir = SEGMENTED_BASE / rel_path
        output_dir.mkdir(parents=True, exist_ok=True)

        for input_file in txt_files:
            output_file = output_dir / input_file.name
            text = input_file.read_text(encoding="utf-8")
            sentences = segment_text(text)
            output_file.write_text("\n".join(sentences), encoding="utf-8")
            print(f"Segmented: {input_file} -> {output_file}")
