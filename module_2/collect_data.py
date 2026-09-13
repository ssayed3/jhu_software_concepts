import json
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from scrape import parse_page, save_data


START_URL = "https://www.thegradcafe.com/survey/"

DATA_FILE = Path("applicant_data.json")
PROGRESS_FILE = Path("scrape_progress.json")
LAST_PAGE_FILE = Path("last_page.html")

TARGET_RECORDS = 30000

BETWEEN_PAGES_WAIT = 2


def run_chrome_javascript(javascript: str) -> str:
    script = f'''
    tell application "Google Chrome"
        set result_text to execute active tab of front window javascript "{javascript}"
        return result_text
    end tell
    '''

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout


def open_url(url: str) -> None:
    script = f'''
    tell application "Google Chrome"
        set URL of active tab of front window to "{url}"
    end tell
    '''

    subprocess.run(
        ["osascript", "-e", script],
        check=True,
    )


def validate_survey_url(url: str) -> bool:
    parsed_url = urlparse(url)

    return (
        parsed_url.scheme in ("http", "https")
        and parsed_url.netloc == "www.thegradcafe.com"
        and parsed_url.path.rstrip("/") == "/survey"
    )


def capture_current_html() -> str:
    return run_chrome_javascript(
        "document.documentElement.outerHTML"
    )


def check_for_block() -> bool:
    page_text = run_chrome_javascript(
        "document.body.innerText"
    )

    block_phrases = [
        "Verify you are human",
        "Checking your browser",
        "Just a moment",
        "Attention Required",
    ]

    for phrase in block_phrases:
        if phrase.lower() in page_text.lower():
            return True

    return False


def get_next_url(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)

        if text == "Next":
            next_url = link["href"]

            if validate_survey_url(next_url):
                return next_url

    return None


def load_existing_data() -> list[dict]:
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    print(f"Loaded {len(data)} existing applicants.")

    return data


def load_progress() -> tuple[int, str]:
    if not PROGRESS_FILE.exists():
        return 1, START_URL

    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        progress = json.load(file)

    page_number = progress["next_page_number"]
    next_url = progress["next_url"]

    print(f"Resuming from page {page_number}.")

    return page_number, next_url


def save_progress(
    next_page_number: int,
    next_url: str,
) -> None:
    progress = {
        "next_page_number": next_page_number,
        "next_url": next_url,
    }

    with open(
        PROGRESS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            progress,
            file,
            indent=4,
            ensure_ascii=False,
        )


def collect_data() -> None:
    all_applicants = load_existing_data()

    seen_urls = {
        applicant["applicant_url"]
        for applicant in all_applicants
        if applicant.get("applicant_url")
    }

    page_number, current_url = load_progress()

    print()
    print("Starting GradCafe collection")
    print(f"Current records: {len(all_applicants)}")
    print(f"Target records: {TARGET_RECORDS}")

    while len(all_applicants) < TARGET_RECORDS:

        if not validate_survey_url(current_url):
            print("Invalid GradCafe survey URL.")
            print("Stopping.")
            return

        print()
        print(f"Processing page {page_number}")
        print(f"Current total: {len(all_applicants)}")

        open_url(current_url)

        print("Waiting for applicant data to load...")

        applicants_loaded = False

        for attempt in range(6):
            time.sleep(5)

            html = capture_current_html()
            soup = BeautifulSoup(html, "html.parser")
            applicants = parse_page(soup)

            if len(applicants) > 0:
                applicants_loaded = True
                break

            print(
                f"No applicants yet. "
                f"Waiting again... ({attempt + 1}/6)"
            )

        if not applicants_loaded:
            print("Applicants did not load after 30 seconds.")
            print("Stopping safely.")
            return

        if check_for_block():
            print()
            print("Verification or blocking page detected.")
            print("Collection has stopped safely.")
            print(
                "Complete the verification manually "
                "in Chrome."
            )
            print(
                "Then run python collect_data.py again."
            )
            return

        LAST_PAGE_FILE.write_text(
            html,
            encoding="utf-8",
        )

        new_records = 0

        for applicant in applicants:
            applicant_url = applicant.get(
                "applicant_url"
            )

            if not applicant_url:
                continue

            if applicant_url in seen_urls:
                continue

            seen_urls.add(applicant_url)
            all_applicants.append(applicant)
            new_records += 1

            if len(all_applicants) >= TARGET_RECORDS:
                break

        save_data(
            all_applicants,
            str(DATA_FILE),
        )

        print(
            f"Found {len(applicants)} applicants "
            "on this page."
        )
        print(
            f"Added {new_records} new applicants."
        )
        print(
            f"Saved total: {len(all_applicants)}"
        )

        if len(all_applicants) >= TARGET_RECORDS:
            print()
            print("Target reached!")
            print(
                f"{len(all_applicants)} applicants "
                f"saved to {DATA_FILE}"
            )
            return

        next_url = get_next_url(html)

        if next_url is None:
            print("No Next link found.")
            print("Stopping.")
            return

        save_progress(
            next_page_number=page_number + 1,
            next_url=next_url,
        )

        current_url = next_url
        page_number += 1

        print(
            f"Waiting {BETWEEN_PAGES_WAIT} seconds "
            "before continuing..."
        )

        time.sleep(BETWEEN_PAGES_WAIT)


if __name__ == "__main__":
    collect_data()