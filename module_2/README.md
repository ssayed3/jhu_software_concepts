# Module 2 - Web Scraping

**Name:** Sayed Sayed  
**JHED:** ssayed3

## Overview

This project collects graduate admissions results from the public GradCafe survey pages, converts the applicant information into structured JSON, and uses the instructor-provided local LLM to standardize program and university names.

The final dataset contains 30,000 unique applicant records.

## Files

- `scrape.py` - HTML parsing and data extraction functions.
- `collect_data.py` - browser-based collection, pagination, duplicate prevention, delays, and resume support.
- `clean.py` - standardizes program and university names with the provided local LLM.
- `applicant_data.json` - 30,000 original scraped applicant records.
- `llm_extend_applicant_data.json` - cleaned dataset with LLM-generated fields.
- `screenshot.jpg` - screenshot showing review of GradCafe robots.txt.
- `llm_hosting/` - instructor-provided LLM application and canonical data.
- `requirements.txt` - required Python packages.

## Robots.txt and Responsible Scraping

Before collecting data, I manually reviewed the GradCafe robots.txt file at:

https://www.thegradcafe.com/robots.txt

A screenshot is included as `screenshot.jpg`.

Only publicly available survey pages were accessed. The program does not log in, bypass CAPTCHA, bypass access controls, or access private pages.

Direct automated HTTP requests returned HTTP 403 responses. Following the course guidance, I used a normal Google Chrome session and captured the rendered HTML from the public survey page.

If a verification or blocking page is detected, collection stops rather than attempting to bypass it.

A delay is included between pages.

## Scraping Approach

`collect_data.py` opens GradCafe survey pages in Google Chrome and captures the rendered HTML through AppleScript.

BeautifulSoup parses the HTML and extracts applicant rows and their associated detail or comment rows.

GradCafe uses cursor-based pagination. The program reads the actual `Next` URL from each page instead of manually constructing page numbers.

The scraper:

1. Loads previously collected records when available.
2. Tracks applicant URLs to prevent duplicates.
3. Opens the current survey page in Chrome.
4. Waits for the applicant table to load.
5. Parses the rendered HTML with BeautifulSoup.
6. Stops safely if verification or blocking is detected.
7. Saves data after each page.
8. Saves pagination progress so collection can resume after interruption.
9. Waits between pages.
10. Stops after collecting 30,000 applicant records.

Final raw data validation:

- 30,000 records
- 30,000 unique applicant URLs
- 0 duplicate applicant URLs

## Extracted Fields

Each record contains the available values for:

- School/university
- Program
- Degree
- Date added
- Decision
- Decision status
- Decision date
- Applicant entry URL
- Admission season
- Citizenship
- GRE quantitative
- GRE verbal
- GRE analytical writing
- GPA
- Comments

Missing values are stored as JSON `null`.

## Data Cleaning

The original scraped fields are preserved.

The cleaning stage uses the instructor-provided TinyLlama application in `llm_hosting/`.

The provided LLM function accepts one text input. Therefore, `clean.py` combines the original program and school values before sending them to the model so that it has both pieces of information.

Unique program-school combinations are cleaned once and reused for matching applicant records. A local cache is also used during processing so interrupted cleaning can resume without repeating completed LLM calls.

The cleaned output adds:

- `llm-generated-program`
- `llm-generated-university`

Final cleaned data validation:

- 30,000 records
- 30,000 unique applicant URLs
- 0 missing LLM-generated program values
- 0 missing LLM-generated university values

## Known Limitations

GradCafe data is user-submitted and may contain inconsistent spelling, abbreviations, formatting, and missing values.

The local LLM can occasionally introduce spelling changes or imperfect standardization. Therefore, the original school and program values are preserved and the LLM results are stored separately.

Some dates are preserved exactly as displayed by GradCafe and may not contain every date component.

The collection workflow was developed on macOS and requires Google Chrome with JavaScript from Apple Events enabled.

## Installation

Create and activate a virtual environment:

    python3 -m venv venv
    source venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

## Running the Scraper

From the `module_2` directory:

    python collect_data.py

The records are saved to `applicant_data.json`.

## Running the Cleaning Process

After the raw dataset has been created:

    python clean.py

The cleaned dataset is saved to:

    llm_extend_applicant_data.json

The local LLM model is downloaded when required. Large downloaded model files are excluded from Git.
