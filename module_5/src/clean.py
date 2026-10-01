"""Clean applicant program and university names using the local LLM."""

import json
import os
import sys
from pathlib import Path

BASE_FOLDER = Path(__file__).resolve().parent
LLM_FOLDER = BASE_FOLDER.parent / "llm_hosting"

os.chdir(LLM_FOLDER)
sys.path.insert(0, str(LLM_FOLDER))


def _call_llm(text):  # pragma: no cover
    """Send text to the locally hosted LLM for standardization."""
    # Imported here intentionally so the LLM app loads only when needed.
    # pylint: disable=import-outside-toplevel,import-error
    from app import _call_llm as real_call_llm

    return real_call_llm(text)


INPUT_FILE = BASE_FOLDER / "applicant_data.json"
OUTPUT_FILE = BASE_FOLDER / "llm_extend_applicant_data.json"
CACHE_FILE = BASE_FOLDER / "llm_cleaning_cache.json"


def load_json(path: Path):
    """Load and return JSON data from the given file path."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, path: Path):
    """Save data as formatted JSON to the given file path."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_cache() -> dict:
    """Load previously cached LLM cleaning results."""
    if CACHE_FILE.exists():
        cache = load_json(CACHE_FILE)
        print(f"Loaded {len(cache)} cached cleaning results.")
        return cache

    return {}


def make_key(program: str, school: str) -> str:
    """Create a unique cache key from a program and school name."""
    return f"{program}|||{school}"


def clean_data() -> None:
    """Clean applicant program and school names and save the results."""
    applicants = load_json(INPUT_FILE)

    unique_pairs = sorted({
        (
            applicant.get("program", ""),
            applicant.get("school", ""),
        )
        for applicant in applicants
    })

    cache = load_cache()

    print(f"Total records: {len(applicants)}")
    print(f"Unique program-school pairs: {len(unique_pairs)}")
    print(f"Already cleaned: {len(cache)}")

    for number, (program, school) in enumerate(
        unique_pairs,
        start=1,
    ):
        key = make_key(program, school)

        if key in cache:
            continue

        combined_text = f"{program}, {school}"

        llm_result = _call_llm(combined_text)

        cache[key] = {
            "llm-generated-program":
                llm_result["standardized_program"],
            "llm-generated-university":
                llm_result["standardized_university"],
        }

        # Save immediately so progress is not lost.
        save_json(cache, CACHE_FILE)

        if number % 100 == 0:
            print(
                f"Progress: {number} of "
                f"{len(unique_pairs)} unique pairs"
            )

    cleaned_applicants = []

    for applicant in applicants:
        program = applicant.get("program", "")
        school = applicant.get("school", "")

        key = make_key(program, school)

        cleaned_applicant = applicant.copy()
        cleaned_applicant.update(cache[key])

        cleaned_applicants.append(cleaned_applicant)

    save_json(cleaned_applicants, OUTPUT_FILE)

    print()
    print("Cleaning complete.")
    print(f"Saved {len(cleaned_applicants)} records.")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":  # pragma: no cover
    clean_data()
