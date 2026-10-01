import pytest
import json
from bs4 import BeautifulSoup

from src import scrape


@pytest.mark.web
def test_validate_url():
    assert scrape.validate_url(
        "https://www.thegradcafe.com/survey/"
    ) is True

    assert scrape.validate_url(
        "http://www.thegradcafe.com/survey/"
    ) is True

    assert scrape.validate_url(
        "https://example.com/survey/"
    ) is False

    assert scrape.validate_url(
        "ftp://www.thegradcafe.com/survey/"
    ) is False


@pytest.mark.web
def test_parse_decision_with_date():
    status, decision_date = scrape.parse_decision(
        "Accepted on Sep 09"
    )

    assert status == "Accepted"
    assert decision_date == "Sep 09"


@pytest.mark.web
def test_parse_decision_without_date():
    status, decision_date = scrape.parse_decision(
        "Waitlisted"
    )

    assert status == "Waitlisted"
    assert decision_date is None


@pytest.mark.web
def test_load_html(tmp_path):
    html_file = tmp_path / "test.html"

    html_file.write_text(
        "<html><body><h1>Hello</h1></body></html>",
        encoding="utf-8"
    )

    soup = scrape.load_html(str(html_file))

    assert soup.find("h1").get_text() == "Hello"

@pytest.mark.web
def test_parse_row():
    html = """
    <table>
        <tr>
            <td>Johns Hopkins University</td>
            <td>
                <span>Computer Science</span>
                <span>Masters</span>
            </td>
            <td>Sep 09, 2026</td>
            <td>Accepted on Sep 10</td>
            <td>
                <a href="/result/12345">View</a>
            </td>
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    result = scrape.parse_row(row)

    assert result["school"] == "Johns Hopkins University"
    assert result["program"] == "Computer Science"
    assert result["degree"] == "Masters"
    assert result["added_on"] == "Sep 09, 2026"
    assert result["decision"] == "Accepted on Sep 10"
    assert result["status"] == "Accepted"
    assert result["decision_date"] == "Sep 10"
    assert result["applicant_url"] == (
        "https://www.thegradcafe.com/result/12345"
    )

    assert result["season"] is None
    assert result["citizenship"] is None
    assert result["gre"] is None
    assert result["gre_v"] is None
    assert result["gre_aw"] is None
    assert result["gpa"] is None
    assert result["comment"] is None

@pytest.mark.web
def test_parse_detail_row_structured():
    html = """
    <tr>
        <td>
            Spring 2027 |
            International |
            GRE 165 |
            GRE V 160 |
            GRE AW 4.5 |
            GPA 3.90
        </td>
    </tr>
    """

    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    result = scrape.parse_detail_row(row)

    assert result["season"] == "Spring 2027"
    assert result["citizenship"] == "International"
    assert result["gre"] == "165"
    assert result["gre_v"] == "160"
    assert result["gre_aw"] == "4.5"
    assert result["gpa"] == "3.90"
    assert result["comment"] is None


@pytest.mark.web
def test_parse_detail_row_comment():
    html = """
    <tr>
        <td>Very excited about this program!</td>
    </tr>
    """

    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    result = scrape.parse_detail_row(row)

    assert result["comment"] == "Very excited about this program!"
    assert result["season"] is None
    assert result["citizenship"] is None


@pytest.mark.web
def test_parse_detail_row_empty():
    html = "<tr><td></td></tr>"

    soup = BeautifulSoup(html, "html.parser")
    row = soup.find("tr")

    result = scrape.parse_detail_row(row)

    assert result == {
        "season": None,
        "citizenship": None,
        "gre": None,
        "gre_v": None,
        "gre_aw": None,
        "gpa": None,
        "comment": None,
    }

@pytest.mark.web
def test_parse_gre_from_comment_all_scores():
    comment = (
        "Quantitative: 165, "
        "Verbal: 160, "
        "Analytical Writing: 4.5"
    )

    result = scrape.parse_gre_from_comment(comment)

    assert result["gre"] == "165"
    assert result["gre_v"] == "160"
    assert result["gre_aw"] == "4.5"


@pytest.mark.web
def test_parse_gre_from_comment_no_comment():
    result = scrape.parse_gre_from_comment(None)

    assert result == {
        "gre": None,
        "gre_v": None,
        "gre_aw": None,
    }


@pytest.mark.web
def test_parse_gre_from_comment_without_scores():
    result = scrape.parse_gre_from_comment(
        "Very excited to receive my acceptance!"
    )

    assert result["gre"] is None
    assert result["gre_v"] is None
    assert result["gre_aw"] is None

@pytest.mark.web
def test_parse_page_with_structured_details():
    html = """
    <table>
        <tr>
            <td>Johns Hopkins University</td>
            <td>
                <span>Computer Science</span>
                <span>Masters</span>
            </td>
            <td>Sep 09, 2026</td>
            <td>Accepted on Sep 10</td>
            <td><a href="/result/12345">View</a></td>
        </tr>

        <tr>
            <td>
                Fall 2026 |
                American |
                GRE 165 |
                GRE V 160 |
                GRE AW 4.5 |
                GPA 3.90
            </td>
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")

    applicants = scrape.parse_page(soup)

    assert len(applicants) == 1

    applicant = applicants[0]

    assert applicant["school"] == "Johns Hopkins University"
    assert applicant["season"] == "Fall 2026"
    assert applicant["citizenship"] == "American"
    assert applicant["gre"] == "165"
    assert applicant["gre_v"] == "160"
    assert applicant["gre_aw"] == "4.5"
    assert applicant["gpa"] == "3.90"

@pytest.mark.web
def test_parse_page_with_comment_details():
    html = """
    <table>
        <tr>
            <td>MIT</td>
            <td>
                <span>Computer Science</span>
                <span>PhD</span>
            </td>
            <td>Sep 09, 2026</td>
            <td>Accepted on Sep 10</td>
            <td><a href="/result/99999">View</a></td>
        </tr>

        <tr>
            <td>
                Quantitative: 168,
                Verbal: 162,
                Analytical Writing: 5.0
            </td>
        </tr>
    </table>
    """

    soup = BeautifulSoup(html, "html.parser")

    applicants = scrape.parse_page(soup)

    assert len(applicants) == 1

    applicant = applicants[0]

    assert "Quantitative: 168" in applicant["comment"]
    assert applicant["gre"] == "168"
    assert applicant["gre_v"] == "162"
    assert applicant["gre_aw"] == "5.0"

@pytest.mark.web
def test_save_data(tmp_path):
    output_file = tmp_path / "applicants.json"

    data = [
        {
            "school": "Johns Hopkins University",
            "program": "Computer Science",
        },
        {
            "school": "MIT",
            "program": "Artificial Intelligence",
        },
    ]

    scrape.save_data(data, str(output_file))

    saved_data = json.loads(
        output_file.read_text(encoding="utf-8")
    )

    assert saved_data == data

@pytest.mark.web
def test_run_chrome_javascript(monkeypatch):
    class FakeResult:
        stdout = "<html>Test Page</html>"

    def fake_run(*args, **kwargs):
        return FakeResult()

    monkeypatch.setattr(
        scrape.subprocess,
        "run",
        fake_run
    )

    result = scrape.run_chrome_javascript(
        "document.documentElement.outerHTML"
    )

    assert result == "<html>Test Page</html>"


@pytest.mark.web
def test_open_url(monkeypatch):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(
        scrape.subprocess,
        "run",
        fake_run
    )

    scrape.open_url(
        "https://www.thegradcafe.com/survey/"
    )

    assert len(calls) == 1
    assert "osascript" in calls[0][0][0]

@pytest.mark.web
def test_validate_survey_url():
    assert scrape.validate_survey_url(
        "https://www.thegradcafe.com/survey/"
    ) is True

    assert scrape.validate_survey_url(
        "https://www.thegradcafe.com/survey"
    ) is True

    assert scrape.validate_survey_url(
        "https://www.thegradcafe.com/result/12345"
    ) is False

    assert scrape.validate_survey_url(
        "https://example.com/survey/"
    ) is False


@pytest.mark.web
def test_capture_current_html(monkeypatch):
    monkeypatch.setattr(
        scrape,
        "run_chrome_javascript",
        lambda javascript: "<html>Captured</html>"
    )

    result = scrape.capture_current_html()

    assert result == "<html>Captured</html>"

@pytest.mark.web
def test_check_for_block_detected(monkeypatch):
    monkeypatch.setattr(
        scrape,
        "run_chrome_javascript",
        lambda javascript: "Please Verify you are human"
    )

    assert scrape.check_for_block() is True


@pytest.mark.web
def test_check_for_block_not_detected(monkeypatch):
    monkeypatch.setattr(
        scrape,
        "run_chrome_javascript",
        lambda javascript: "Normal GradCafe applicant page"
    )

    assert scrape.check_for_block() is False

@pytest.mark.web
def test_get_next_url_found():
    html = """
    <html>
        <body>
            <a href="https://www.thegradcafe.com/survey/?page=2">
                Next
            </a>
        </body>
    </html>
    """

    result = scrape.get_next_url(html)

    assert result == (
        "https://www.thegradcafe.com/survey/?page=2"
    )


@pytest.mark.web
def test_get_next_url_not_found():
    html = """
    <html>
        <body>
            <a href="https://www.thegradcafe.com/survey/?page=2">
                Previous
            </a>
        </body>
    </html>
    """

    result = scrape.get_next_url(html)

    assert result is None

@pytest.mark.web
def test_load_existing_data_missing(monkeypatch, tmp_path):
    data_file = tmp_path / "applicant_data.json"

    monkeypatch.setattr(
        scrape,
        "DATA_FILE",
        data_file
    )

    result = scrape.load_existing_data()

    assert result == []


@pytest.mark.web
def test_load_existing_data_existing(monkeypatch, tmp_path):
    data_file = tmp_path / "applicant_data.json"

    data = [
        {
            "school": "Johns Hopkins University",
            "applicant_url": "https://www.thegradcafe.com/result/1",
        }
    ]

    data_file.write_text(
        json.dumps(data),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        scrape,
        "DATA_FILE",
        data_file
    )

    result = scrape.load_existing_data()

    assert result == data

@pytest.mark.web
def test_load_progress_missing(monkeypatch, tmp_path):
    progress_file = tmp_path / "scrape_progress.json"

    monkeypatch.setattr(
        scrape,
        "PROGRESS_FILE",
        progress_file
    )

    page_number, next_url = scrape.load_progress()

    assert page_number == 1
    assert next_url == scrape.START_URL


@pytest.mark.web
def test_load_progress_existing(monkeypatch, tmp_path):
    progress_file = tmp_path / "scrape_progress.json"

    progress = {
        "next_page_number": 5,
        "next_url": "https://www.thegradcafe.com/survey/?page=5",
    }

    progress_file.write_text(
        json.dumps(progress),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        scrape,
        "PROGRESS_FILE",
        progress_file
    )

    page_number, next_url = scrape.load_progress()

    assert page_number == 5
    assert next_url == (
        "https://www.thegradcafe.com/survey/?page=5"
    )

@pytest.mark.web
def test_save_progress(monkeypatch, tmp_path):
    progress_file = tmp_path / "scrape_progress.json"

    monkeypatch.setattr(
        scrape,
        "PROGRESS_FILE",
        progress_file
    )

    scrape.save_progress(
        next_page_number=6,
        next_url="https://www.thegradcafe.com/survey/?page=6"
    )

    saved = json.loads(
        progress_file.read_text(encoding="utf-8")
    )

    assert saved["next_page_number"] == 6
    assert saved["next_url"] == (
        "https://www.thegradcafe.com/survey/?page=6"
    )

@pytest.mark.web
def test_collect_data_invalid_url(monkeypatch):
    monkeypatch.setattr(
        scrape,
        "load_existing_data",
        lambda: []
    )

    monkeypatch.setattr(
        scrape,
        "load_progress",
        lambda: (1, "https://example.com/not-gradcafe")
    )

    monkeypatch.setattr(
        scrape,
        "NEW_RECORDS_PER_RUN",
        1
    )

    scrape.collect_data()

@pytest.mark.web
def test_collect_data_no_applicants_loaded(monkeypatch):
    monkeypatch.setattr(
        scrape,
        "load_existing_data",
        lambda: []
    )

    monkeypatch.setattr(
        scrape,
        "load_progress",
        lambda: (1, scrape.START_URL)
    )

    monkeypatch.setattr(
        scrape,
        "NEW_RECORDS_PER_RUN",
        1
    )

    monkeypatch.setattr(
        scrape,
        "open_url",
        lambda url: None
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None
    )

    monkeypatch.setattr(
        scrape,
        "capture_current_html",
        lambda: "<html><body>No applicants</body></html>"
    )

    scrape.collect_data()

@pytest.mark.web
def test_collect_data_block_detected(monkeypatch):
    monkeypatch.setattr(
        scrape,
        "load_existing_data",
        lambda: []
    )

    monkeypatch.setattr(
        scrape,
        "load_progress",
        lambda: (1, scrape.START_URL)
    )

    monkeypatch.setattr(
        scrape,
        "NEW_RECORDS_PER_RUN",
        1
    )

    monkeypatch.setattr(
        scrape,
        "open_url",
        lambda url: None
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None
    )

    monkeypatch.setattr(
        scrape,
        "capture_current_html",
        lambda: "<html>Applicant page</html>"
    )

    monkeypatch.setattr(
        scrape,
        "parse_page",
        lambda soup: [
            {
                "applicant_url":
                    "https://www.thegradcafe.com/result/1"
            }
        ]
    )

    monkeypatch.setattr(
        scrape,
        "check_for_block",
        lambda: True
    )

    scrape.collect_data()

@pytest.mark.web
def test_collect_data_reaches_target(monkeypatch, tmp_path):
    applicant = {
        "school": "Johns Hopkins University",
        "applicant_url":
            "https://www.thegradcafe.com/result/12345"
    }

    monkeypatch.setattr(
        scrape,
        "load_existing_data",
        lambda: []
    )

    monkeypatch.setattr(
        scrape,
        "load_progress",
        lambda: (1, scrape.START_URL)
    )

    monkeypatch.setattr(
        scrape,
        "NEW_RECORDS_PER_RUN",
        1
    )

    monkeypatch.setattr(
        scrape,
        "LAST_PAGE_FILE",
        tmp_path / "last_page.html"
    )

    monkeypatch.setattr(
        scrape,
        "DATA_FILE",
        tmp_path / "applicant_data.json"
    )

    monkeypatch.setattr(
        scrape,
        "open_url",
        lambda url: None
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None
    )

    monkeypatch.setattr(
        scrape,
        "capture_current_html",
        lambda: "<html>Applicant page</html>"
    )

    monkeypatch.setattr(
        scrape,
        "parse_page",
        lambda soup: [applicant]
    )

    monkeypatch.setattr(
        scrape,
        "check_for_block",
        lambda: False
    )

    scrape.collect_data()

    saved = json.loads(
        (tmp_path / "applicant_data.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(saved) == 1
    assert saved[0]["school"] == "Johns Hopkins University"

    assert (
        tmp_path / "last_page.html"
    ).read_text(encoding="utf-8") == (
        "<html>Applicant page</html>"
    )

@pytest.mark.web
def test_collect_data_skips_invalid_and_duplicate_then_no_next(
    monkeypatch,
    tmp_path
):
    existing = [
        {
            "school": "Existing School",
            "applicant_url":
                "https://www.thegradcafe.com/result/existing"
        }
    ]

    applicants = [
        {
            "school": "Missing URL",
            "applicant_url": None
        },
        {
            "school": "Duplicate",
            "applicant_url":
                "https://www.thegradcafe.com/result/existing"
        }
    ]

    monkeypatch.setattr(
        scrape,
        "load_existing_data",
        lambda: existing.copy()
    )

    monkeypatch.setattr(
        scrape,
        "load_progress",
        lambda: (1, scrape.START_URL)
    )

    monkeypatch.setattr(
        scrape,
        "NEW_RECORDS_PER_RUN",
        1
    )

    monkeypatch.setattr(
        scrape,
        "LAST_PAGE_FILE",
        tmp_path / "last_page.html"
    )

    monkeypatch.setattr(
        scrape,
        "DATA_FILE",
        tmp_path / "applicant_data.json"
    )

    monkeypatch.setattr(scrape, "open_url", lambda url: None)
    monkeypatch.setattr(scrape.time, "sleep", lambda seconds: None)

    monkeypatch.setattr(
        scrape,
        "capture_current_html",
        lambda: "<html>Page</html>"
    )

    monkeypatch.setattr(
        scrape,
        "parse_page",
        lambda soup: applicants
    )

    monkeypatch.setattr(
        scrape,
        "check_for_block",
        lambda: False
    )

    monkeypatch.setattr(
        scrape,
        "get_next_url",
        lambda html: None
    )

    scrape.collect_data()

@pytest.mark.web
def test_collect_data_continues_to_next_page(monkeypatch, tmp_path):
    page_calls = {"count": 0}
    saved_progress = []

    applicant = {
        "school": "Johns Hopkins University",
        "applicant_url":
            "https://www.thegradcafe.com/result/new"
    }

    monkeypatch.setattr(
        scrape,
        "load_existing_data",
        lambda: []
    )

    monkeypatch.setattr(
        scrape,
        "load_progress",
        lambda: (1, scrape.START_URL)
    )

    monkeypatch.setattr(
        scrape,
        "NEW_RECORDS_PER_RUN",
        2
    )

    monkeypatch.setattr(
        scrape,
        "LAST_PAGE_FILE",
        tmp_path / "last_page.html"
    )

    monkeypatch.setattr(
        scrape,
        "DATA_FILE",
        tmp_path / "applicant_data.json"
    )

    monkeypatch.setattr(
        scrape,
        "open_url",
        lambda url: None
    )

    monkeypatch.setattr(
        scrape.time,
        "sleep",
        lambda seconds: None
    )

    monkeypatch.setattr(
        scrape,
        "capture_current_html",
        lambda: "<html>Page</html>"
    )

    def fake_parse_page(soup):
        page_calls["count"] += 1

        if page_calls["count"] == 1:
            return [applicant]

        return []

    monkeypatch.setattr(
        scrape,
        "parse_page",
        fake_parse_page
    )

    monkeypatch.setattr(
        scrape,
        "check_for_block",
        lambda: False
    )

    monkeypatch.setattr(
        scrape,
        "get_next_url",
        lambda html:
            "https://www.thegradcafe.com/survey/?page=2"
    )

    monkeypatch.setattr(
        scrape,
        "save_progress",
        lambda next_page_number, next_url:
            saved_progress.append(
                (next_page_number, next_url)
            )
    )

    scrape.collect_data()

    assert saved_progress == [
        (
            2,
            "https://www.thegradcafe.com/survey/?page=2"
        )
    ]