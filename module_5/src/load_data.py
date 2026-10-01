"""Load applicant JSON records into the PostgreSQL database."""

import json
from datetime import datetime
from pathlib import Path

from src.db_config import get_db_settings, get_psycopg_connection


BASE_FOLDER = Path(__file__).resolve().parent

LLM_DATA_FILE = BASE_FOLDER / "llm_extend_applicant_data.json"
SCRAPED_DATA_FILE = BASE_FOLDER / "applicant_data.json"


def create_table(conn):
    """Create the applicants table if it does not already exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                p_id SERIAL PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT UNIQUE,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            );
        """)


def parse_date(date_string):
    """Convert a date string into a Python date object."""
    if not date_string:
        return None

    try:
        return datetime.strptime(date_string, "%b %d, %Y").date()
    except ValueError:
        return None


def parse_number(value):
    """Convert a numeric value to float, returning None if invalid."""
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def load_applicants(conn, data_file=LLM_DATA_FILE):
    """Insert applicant records from a JSON file into PostgreSQL."""
    with open(data_file, "r", encoding="utf-8") as file:
        applicants = json.load(file)

    inserted = 0

    with conn.cursor() as cur:
        for applicant in applicants:
            school = applicant.get("school", "")
            program_name = applicant.get("program", "")

            # Keep the original university and program together.
            program = f"{school}, {program_name}"

            cur.execute("""
                INSERT INTO applicants (
                    program,
                    comments,
                    date_added,
                    url,
                    status,
                    term,
                    us_or_international,
                    gpa,
                    gre,
                    gre_v,
                    gre_aw,
                    degree,
                    llm_generated_program,
                    llm_generated_university
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (url) DO NOTHING;
            """, (
                program,
                applicant.get("comment"),
                parse_date(applicant.get("added_on")),
                applicant.get("applicant_url"),
                applicant.get("status"),
                applicant.get("season"),
                applicant.get("citizenship"),
                parse_number(applicant.get("gpa")),
                parse_number(applicant.get("gre")),
                parse_number(applicant.get("gre_v")),
                parse_number(applicant.get("gre_aw")),
                applicant.get("degree"),
                applicant.get("llm-generated-program"),
                applicant.get("llm-generated-university")
            ))

            inserted += cur.rowcount

    return inserted


def load_scraped_data():
    """Load newly scraped applicant records into PostgreSQL."""
    print("Loading newly scraped data into PostgreSQL...")

    with get_psycopg_connection() as conn:
        inserted = load_applicants(
            conn,
            data_file=SCRAPED_DATA_FILE
        )

        conn.commit()

    return inserted


def main():
    """Connect to PostgreSQL and load the LLM-cleaned applicant data."""
    print("Connecting to PostgreSQL...")

    with get_psycopg_connection() as conn:
        inserted = load_applicants(
            conn,
            data_file=LLM_DATA_FILE
        )

        conn.commit()

        print(f"Database: {get_db_settings()['dbname']}")
        print(f"New applicants inserted: {inserted}")
        print("Data loading complete.")


if __name__ == "__main__":  # pragma: no cover
    main()
