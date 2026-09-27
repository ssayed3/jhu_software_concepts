import pytest

from src.app import create_app, scrape_lock

def fake_scraper():
    return [
        {
            "school": "Test University",
            "program": "Computer Science",
            "degree": "Masters",
            "applicant_url": "https://example.com/integration-1"
        },
        {
            "school": "Example University",
            "program": "Data Science",
            "degree": "PhD",
            "applicant_url": "https://example.com/integration-2"
        }
    ]


loaded_rows = []


def fake_loader(rows):
    loaded_rows.extend(rows)

def fake_analysis():
    if loaded_rows:
        return [
            {
                "question": "How many applicants were loaded?",
                "answer": str(len(loaded_rows))
            }
        ]

    return [
        {
            "question": "How many applicants were loaded?",
            "answer": "0"
        }
    ]

@pytest.mark.integration
def test_end_to_end_workflow():
    loaded_rows.clear()

    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis,
        scraper_func=fake_scraper,
        loader_func=fake_loader
    )

    client = app.test_client()

    pull_response = client.post("/pull-data")
    assert pull_response.status_code == 200
    assert len(loaded_rows) == 2

    update_response = client.post("/update-analysis")
    assert update_response.status_code == 200

    page_response = client.get("/analysis")
    assert page_response.status_code == 200
    assert b"How many applicants were loaded?" in page_response.data
    assert b"Answer:" in page_response.data
    assert b"2" in page_response.data

@pytest.mark.integration
def test_overlapping_pulls():
    scrape_lock.acquire()

    try:
        app = create_app(
            {"TESTING": True},
            analysis_func=fake_analysis,
            scraper_func=fake_scraper,
            loader_func=fake_loader
        )

        client = app.test_client()

        response = client.post("/pull-data")

        assert response.status_code == 409
        assert response.get_json() == {"busy": True}

    finally:
        scrape_lock.release()