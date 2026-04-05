# Visits known BoB programme pages and extracts citations per period.
# Writes all citations to data/raw/bbc_radio4/<period>/citations.txt.

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from bob_scraper import SESSION_FILE, PROJECT_ROOT, _extract_citation, _do_login, PAGE_DELAY

DATA_DIR = PROJECT_ROOT / "data" / "raw" / "bbc_radio4"

CONTROL_SOURCES = {
    "Jun 2016": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0CA2AF50?bcast=121835602",
    "Jul 2016": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0CC699B0?bcast=121975586",
    "Aug 2016": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0CFFA856?bcast=122208214",
    "Sep 2016": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0D29087C?bcast=122411775",
    "Oct 2016": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0D778C31?bcast=122623156",
    "Nov 2016": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0DB0BC53?bcast=122816640",
    "Dec 2016": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0DD95BB7?bcast=123032536",
    "Jan 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0E0377CC?bcast=123234117",
    "Feb 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0E412E01?bcast=123436252",
    "Mar 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0E6D5738?bcast=123630699",
    "Apr 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0EA1672A?bcast=123856417",
    "May 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0EC84064?bcast=124044523",
    "Jun 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0EF47927?bcast=124255506",
    "Jul 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0F2C2187?bcast=124473474",
    "Aug 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0F51BC00?bcast=124662642",
    "Sep 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0F7BF844?bcast=124967469",
    "Oct 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0FB6C598?bcast=125239123",
    "Nov 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/0FF583B4?bcast=125445784",
    "Dec 2017": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1025BF3A?bcast=125643797",
    "Jan 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/104B7965?bcast=125836117",
    "Feb 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/108B084C?bcast=126029360",
    "Mar 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/10B6AD78?bcast=126216576",
    "Apr 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/10EB8ACA?bcast=126429075",
    "May 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/111916A2?bcast=126618282",
    "Jun 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/114A109D?bcast=126816290",
    "Jul 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1183BECD?bcast=127008202",
    "Aug 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/11B11D56?bcast=127207613",
    "Sep 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/11DF676D?bcast=127420373",
    "Oct 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/11FC86DE?bcast=127649748",
    "Nov 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/121FBD94?bcast=127810665",
    "Dec 2018": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1253D17D?bcast=128025335",
    "Jan 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/12825792?bcast=128214849",
    "Feb 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/12B40471?bcast=128408186",
    "Mar 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/12DD4ACD?bcast=128604018",
    "Apr 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/130F1414?bcast=128814154",
    "May 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/133E7714?bcast=129024082",
    "Jun 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/13767034?bcast=129252913",
    "Jul 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/13E6C588?bcast=129611898",
    "Aug 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1418F21C?bcast=129821941",
    "Sep 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/14540246?bcast=130035648",
    "Oct 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1482E62F?bcast=130318363",
    "Nov 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/14B64D6F?bcast=130529007",
}

COVID_SOURCES: dict[str, str] = {
    "Dec 2019": "https://learningonscreen.ac.uk/ondemand/index.php/prog/14E72FAA?bcast=130741838",
    "Jan 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/150A1D22?bcast=130975745",
    "Feb 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1556C343?bcast=131184898",
    "Mar 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/158C2A5C?bcast=131382057",
    "Apr 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/15BA8B1F?bcast=131598454",
    "May 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/15EC0A18?bcast=131826490",
    "Jun 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1625EF32?bcast=132048621",
    "Jul 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/164FDB62?bcast=132264306",
    "Aug 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/168A2873?bcast=132496819",
    "Sep 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/16C653D5?bcast=132702770",
    "Oct 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/16FADA08?bcast=132915333",
    "Nov 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/173EDB8E?bcast=133146931",
    "Dec 2020": "https://learningonscreen.ac.uk/ondemand/index.php/prog/1764705E?bcast=133340900",
    "Jan 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/178E64A2?bcast=133573067",
    "Feb 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/17C5EBCE?bcast=133764586",
    "Mar 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/17EDAB30?bcast=133965990",
    "Apr 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/18180649?bcast=134181828",
    "May 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/18392CD3?bcast=134391271",
    "Jun 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/18503C65?bcast=134602650",
    "Jul 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/18679595?bcast=134784991",
    "Aug 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/187ABCBE?bcast=134994528",
    "Sep 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/18856C65?bcast=135238651",
    "Oct 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/188E2AA0?bcast=135370989",
    "Nov 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/004C4387?bcast=135555522",
    "Dec 2021": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BE8CD76?bcast=135764823",
    "Jan 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BEACD3F?bcast=135954670",
    "Feb 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BED7CF8?bcast=136121581",
    "Mar 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BEF9CF9?bcast=136287395",
    "Apr 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BF1B5B2?bcast=136476943",
    "May 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BF42757?bcast=136658173",
    "Jun 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BF6080E?bcast=136839575",
    "Jul 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BF7D5B2?bcast=137013711",
    "Aug 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BFA0518?bcast=137193817",
    "Sep 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BFBBD81?bcast=137373457",
    "Oct 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BFDECDA?bcast=137570272",
    "Nov 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3BFFF00E?bcast=137760829",
    "Dec 2022": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3C01BE71?bcast=137929310",
    "Jan 2023": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3C03AA22?bcast=138117107",
    "Feb 2023": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3C07AEAA?bcast=138284277",
    "Mar 2023": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3C09AEFA?bcast=138460653",
    "Apr 2023": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3C0C09C4?bcast=138669786",
    "May 2023": "https://learningonscreen.ac.uk/ondemand/index.php/prog/3C0DB7CA?bcast=138825082",
}

SOURCES = {
    "control": CONTROL_SOURCES,
    "covid": COVID_SOURCES,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape BoB citations for bbc_radio4")
    parser.add_argument("--period", choices=["control", "covid"], required=True)
    args = parser.parse_args()

    sources = SOURCES[args.period]
    if not sources:
        print(f"No URLs defined for period '{args.period}' yet.")
        print("Run the audio downloader with --dry-run --overwrite to recover URLs,")
        print("then add them to COVID_SOURCES in this script.")
        sys.exit(1)

    out_path = DATA_DIR / args.period / "citations.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        if SESSION_FILE.exists():
            context = browser.new_context(storage_state=str(SESSION_FILE))
            page = context.new_page()
            page.goto("https://learningonscreen.ac.uk/ondemand/")
            page.wait_for_load_state("domcontentloaded")
            if "login" in page.url or "shibboleth" in page.url.lower():
                print("Session expired — please log in again.")
                SESSION_FILE.unlink()
                context.close()
                context = browser.new_context()
                page = context.new_page()
                _do_login(page)
                context.storage_state(path=str(SESSION_FILE))
            else:
                print("Loaded saved session.")
        else:
            context = browser.new_context()
            page = context.new_page()
            _do_login(page)
            context.storage_state(path=str(SESSION_FILE))

        lines = []
        for month_label, url in sources.items():
            print(f"  [{month_label}] {url}")
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(PAGE_DELAY)

            citation = _extract_citation(page)
            if citation:
                print(f"    → {citation[:80]}")
                lines.append(f"[{month_label}]\n{citation}\nSource: {url}\n")
            else:
                print(f"    WARNING: no citation found")
                lines.append(f"[{month_label}]\nCITATION NOT FOUND\nSource: {url}\n")

        browser.close()

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved {len(lines)} citations → {out_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
