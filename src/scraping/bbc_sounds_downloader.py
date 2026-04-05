# Downloads BBC Sounds audio by intercepting the DASH manifest URL via Playwright,
# then handing it to ffmpeg to save as .m4a.

import argparse
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
SESSION_FILE = PROJECT_ROOT / "bbc_sounds_session.json"

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

MANIFEST_TIMEOUT_MS = 60_000  # ms to wait for the manifest URL to appear


def intercept_manifest(page, sounds_url: str) -> str | None:
    manifest_url = None

    def handle_request(request):
        nonlocal manifest_url
        if ".mpd" in request.url and manifest_url is None:
            print(f"  [manifest] {request.url[:100]}")
            manifest_url = request.url

    page.on("request", handle_request)
    page.goto(sounds_url)

    try:
        page.wait_for_load_state("networkidle", timeout=30_000)  # wait for login/consent redirect to settle
    except Exception:
        pass

    PLAY_SELECTORS = [  # try each in order until one works
        "[data-testid='play-button']",
        "[data-testid='hero-play-button']",
        "button[aria-label='Play']",
        "button[aria-label*='Play']",
        "button[title*='Play']",
        "[class*='play-button']",
        "[class*='PlayButton']",
        "button.sc-c-play-pause-button",
    ]
    clicked = False
    for sel in PLAY_SELECTORS:
        try:
            page.click(sel, timeout=3_000)
            print(f"  Clicked play via: {sel}")
            clicked = True
            break
        except Exception:
            continue

    if not clicked:
        print("  Could not find play button automatically.")
        print("  >>> Please click Play in the browser window <<<")

    # page.wait_for_timeout() pumps Playwright's event loop so request events are
    # delivered to Python; time.sleep() would not.
    deadline = time.time() + MANIFEST_TIMEOUT_MS / 1000
    while manifest_url is None and time.time() < deadline:
        page.wait_for_timeout(300)

    page.remove_listener("request", handle_request)
    return manifest_url


def download_audio(manifest_url: str, output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".tmp.m4a")

    cmd = [
        "ffmpeg", "-y",
        "-i", manifest_url,
        "-vn",              # audio only
        "-acodec", "copy",  # copy without re-encoding
        str(tmp_path)
    ]

    print(f"  Downloading via ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR: ffmpeg failed:")
        print(result.stderr[-1000:])
        if tmp_path.exists():
            tmp_path.unlink()
        return False

    tmp_path.rename(output_path)
    size_mb = output_path.stat().st_size / 1_048_576
    print(f"  Saved {size_mb:.1f} MB → {output_path.relative_to(PROJECT_ROOT)}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Download BBC Sounds audio via DASH interception")
    parser.add_argument("--url", help="Single BBC Sounds URL to download")
    parser.add_argument("--out", help="Output .m4a file path (required with --url)")
    parser.add_argument(
        "--source", default="bbc_radio4",
        help="Source name under data/raw/ (default: bbc_radio4)"
    )
    parser.add_argument(
        "--period", choices=["covid", "control"], default="covid",
        help="Period subfolder (default: covid)"
    )
    parser.add_argument(
        "--year", type=int,
        help="Year for output path (required with --url if --out not given)"
    )
    parser.add_argument(
        "--month", type=int,
        help="Month number for output path (required with --url if --out not given)"
    )
    args = parser.parse_args()

    if not args.url:
        print("--url is required (bulk Genome mode not yet implemented)")
        sys.exit(1)

    # Determine output path
    if args.out:
        out_path = Path(args.out)
    elif args.year and args.month:
        month_name = MONTH_NAMES[args.month]
        out_path = (DATA_DIR / args.source / args.period
                    / str(args.year) / f"{month_name} {args.year}.m4a")
    else:
        print("Provide either --out or both --year and --month")
        sys.exit(1)

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"Already downloaded: {out_path}")
        sys.exit(0)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        # Reuse saved session to help with geo-restrictions
        if SESSION_FILE.exists():
            context = browser.new_context(storage_state=str(SESSION_FILE))
        else:
            context = browser.new_context()

        page = context.new_page()

        print(f"Loading: {args.url}")
        manifest = intercept_manifest(page, args.url)
        context.storage_state(path=str(SESSION_FILE))  # persist session for next run

        if not manifest:
            print("ERROR: Could not intercept DASH manifest URL.")
            print("Make sure the audio starts playing in the browser window.")
            browser.close()
            sys.exit(1)

        print(f"  Manifest intercepted: {manifest[:80]}...")
        browser.close()

    download_audio(manifest, out_path)


if __name__ == "__main__":
    main()
