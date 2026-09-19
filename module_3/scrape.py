from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup


BASE_URL = "https://www.thegradcafe.com/"


def validate_url(url: str) -> bool:
    parsed_url = urlparse(url)

    return (
        parsed_url.scheme in ("http", "https")
        and parsed_url.netloc == "www.thegradcafe.com"
    )


def load_html(file_path: str) -> BeautifulSoup:
    html = Path(file_path).read_text(encoding="utf-8")
    return BeautifulSoup(html, "html.parser")


def parse_decision(decision: str) -> tuple[str, str | None]:
    if " on " in decision:
        status, decision_date = decision.split(" on ", 1)
        return status, decision_date

    return decision, None


def parse_row(row) -> dict:
    cells = row.find_all("td")

    school = cells[0].get_text(strip=True)

    program_spans = cells[1].find_all("span")
    program = program_spans[0].get_text(strip=True)
    degree = program_spans[1].get_text(strip=True)

    added_on = cells[2].get_text(strip=True)

    decision = cells[3].get_text(strip=True)
    status, decision_date = parse_decision(decision)

    link = cells[4].find("a")
    applicant_url = BASE_URL.rstrip("/") + link["href"]

    return {
        "school": school,
        "program": program,
        "degree": degree,
        "added_on": added_on,
        "decision": decision,
        "status": status,
        "decision_date": decision_date,
        "applicant_url": applicant_url,
        "season": None,
        "citizenship": None,
        "gre": None,
        "gre_v": None,
        "gre_aw": None,
        "gpa": None,
        "comment": None,
    }


def parse_detail_row(row) -> dict:
    text = row.get_text(" | ", strip=True)

    details = {
        "season": None,
        "citizenship": None,
        "gre": None,
        "gre_v": None,
        "gre_aw": None,
        "gpa": None,
        "comment": None,
    }

    if not text:
        return details

    parts = [part.strip() for part in text.split("|")]

    structured = False

    for part in parts:
        if part.startswith(("Spring ", "Fall ")):
            details["season"] = part
            structured = True

        elif part in ("International", "American", "Other"):
            details["citizenship"] = part
            structured = True

        elif part.startswith("GRE V "):
            details["gre_v"] = part.replace("GRE V ", "")
            structured = True

        elif part.startswith("GRE AW "):
            details["gre_aw"] = part.replace("GRE AW ", "")
            structured = True

        elif part.startswith("GRE "):
            details["gre"] = part.replace("GRE ", "")
            structured = True

        elif part.startswith("GPA "):
            details["gpa"] = part.replace("GPA ", "")
            structured = True

    if not structured:
        details["comment"] = text

    return details


def parse_gre_from_comment(comment: str | None) -> dict:
    values = {
        "gre": None,
        "gre_v": None,
        "gre_aw": None,
    }

    if not comment:
        return values

    if "Quantitative:" in comment:
        quantitative = (
            comment.split("Quantitative:", 1)[1]
            .split(",", 1)[0]
            .strip()
        )
        values["gre"] = quantitative

    if "Verbal:" in comment:
        verbal = (
            comment.split("Verbal:", 1)[1]
            .split(",", 1)[0]
            .strip()
        )
        values["gre_v"] = verbal

    if "Analytical Writing:" in comment:
        writing = (
            comment.split("Analytical Writing:", 1)[1]
            .strip()
        )
        values["gre_aw"] = writing

    return values


def parse_page(soup: BeautifulSoup) -> list[dict]:
    rows = soup.find_all("tr")
    applicants = []

    current_applicant = None

    for row in rows:
        cells = row.find_all("td")

        if len(cells) == 5:
            current_applicant = parse_row(row)
            applicants.append(current_applicant)

        elif len(cells) == 1 and current_applicant is not None:
            extra = parse_detail_row(row)

            if extra["comment"]:
                current_applicant["comment"] = extra["comment"]

                gre_from_comment = parse_gre_from_comment(
                    extra["comment"]
                )

                if current_applicant["gre"] is None:
                    current_applicant["gre"] = (
                        gre_from_comment["gre"]
                    )

                if current_applicant["gre_v"] is None:
                    current_applicant["gre_v"] = (
                        gre_from_comment["gre_v"]
                    )

                if current_applicant["gre_aw"] is None:
                    current_applicant["gre_aw"] = (
                        gre_from_comment["gre_aw"]
                    )

            else:
                for key in (
                    "season",
                    "citizenship",
                    "gre",
                    "gre_v",
                    "gre_aw",
                    "gpa",
                ):
                    if extra[key] is not None:
                        current_applicant[key] = extra[key]

    return applicants


def save_data(data: list[dict], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


START_URL = "https://www.thegradcafe.com/survey/"

DATA_FILE = Path("applicant_data.json")
PROGRESS_FILE = Path("scrape_progress.json")
LAST_PAGE_FILE = Path("last_page.html")

NEW_RECORDS_PER_RUN = 100

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

    target_records = len(all_applicants) + NEW_RECORDS_PER_RUN

    print(f"Target records for this run: {target_records}")

    while len(all_applicants) < target_records:

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
                "Then run python scrape.py again."
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

            if len(all_applicants) >= target_records:
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

        if len(all_applicants) >= target_records:
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