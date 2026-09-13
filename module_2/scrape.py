from __future__ import annotations

import json
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
        quantitative = comment.split("Quantitative:", 1)[1].split(",", 1)[0].strip()
        values["gre"] = quantitative

    if "Verbal:" in comment:
        verbal = comment.split("Verbal:", 1)[1].split(",", 1)[0].strip()
        values["gre_v"] = verbal

    if "Analytical Writing:" in comment:
        writing = comment.split("Analytical Writing:", 1)[1].strip()
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



