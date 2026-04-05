# Transcribes all .m4a files under data/raw/<source>/<period>/ using OpenAI Whisper.
# Output .txt files feed directly into the cleanse → segment → filter pipeline.

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"


def transcribe(source: str, period: str, model_name: str) -> None:
    import whisper  # deferred so the script is importable without whisper installed

    audio_dir = DATA_DIR / source / period
    audio_files = sorted(audio_dir.rglob("*.m4a"))

    if not audio_files:
        print(f"No .m4a files found under {audio_dir}")
        return

    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)

    for audio_path in audio_files:
        txt_path = audio_path.with_suffix(".txt")
        if txt_path.exists() and txt_path.stat().st_size > 0:
            print(f"[SKIP] {audio_path.name} — transcript already exists")
            continue

        print(f"Transcribing: {audio_path.relative_to(PROJECT_ROOT)}")
        result = model.transcribe(str(audio_path), language="en", fp16=False)
        txt_path.write_text(result["text"], encoding="utf-8")
        print(f"  Saved → {txt_path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper transcription of downloaded audio")
    parser.add_argument("--source", required=True, help="Source name under data/raw/")
    parser.add_argument("--period", choices=["covid", "control"], required=True)
    parser.add_argument(
        "--model", default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    args = parser.parse_args()
    transcribe(args.source, args.period, args.model)


if __name__ == "__main__":
    main()
