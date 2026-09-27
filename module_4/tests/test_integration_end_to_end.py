import os
import pytest
import psycopg

from src.app import create_app, scrape_lock
from src import load_data

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

def fake_scraper_with_overlap():
    return [
        {
            "school": "Example University",
            "program": "Data Science",
            "degree": "PhD",
            "applicant_url": "https://example.com/integration-2"
        },
        {
            "school": "Another University",
            "program": "Artificial Intelligence",
            "degree": "Masters",
            "applicant_url": "https://example.com/integration-3"
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

@pytest.mark.integration
def test_end_to_end_with_postgresql():
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sayedsayed@/module4_test_db"
    )

    # Start with a clean applicants table
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS applicants")
        conn.commit()

    # Create the real PostgreSQL table
    with psycopg.connect(database_url) as conn:
        load_data.create_table(conn)

    # Real loader: inserts the fake scraper rows into PostgreSQL
    def database_loader(rows):
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                delete=False
        ) as temp_file:
            json.dump(rows, temp_file)
            temp_path = temp_file.name

        try:
            with psycopg.connect(database_url) as conn:
                return load_data.load_applicants(conn, temp_path)
        finally:
            os.remove(temp_path)

    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis,
        scraper_func=fake_scraper,
        loader_func=database_loader
    )

    client = app.test_client()

    # Pull fake data through the Flask endpoint
    pull_response = client.post("/pull-data")

    assert pull_response.status_code == 200
    assert pull_response.get_json() == {"ok": True}

    # Verify that the two records really reached PostgreSQL
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants")
            count = cur.fetchone()[0]

    assert count == 2

    # Update analysis
    update_response = client.post("/update-analysis")
    assert update_response.status_code == 200

    # Render analysis page
    page_response = client.get("/analysis")
    assert page_response.status_code == 200
    assert b"Analysis" in page_response.data
    assert b"Answer:" in page_response.data

@pytest.mark.integration
def test_multiple_pulls_with_overlapping_data():
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sayedsayed@/module4_test_db"
    )

    # Start with a clean applicants table
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS applicants")
        conn.commit()

    with psycopg.connect(database_url) as conn:
        load_data.create_table(conn)

    def database_loader(rows):
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False
        ) as temp_file:
            json.dump(rows, temp_file)
            temp_path = temp_file.name

        try:
            with psycopg.connect(database_url) as conn:
                return load_data.load_applicants(conn, temp_path)
        finally:
            os.remove(temp_path)

    # First pull: records 1 and 2
    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis,
        scraper_func=fake_scraper,
        loader_func=database_loader
    )

    client = app.test_client()

    first_response = client.post("/pull-data")
    assert first_response.status_code == 200

    # Second pull: records 2 and 3
    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis,
        scraper_func=fake_scraper_with_overlap,
        loader_func=database_loader
    )

    client = app.test_client()

    second_response = client.post("/pull-data")
    assert second_response.status_code == 200

    # There should be 3 unique records, not 4
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants")
            count = cur.fetchone()[0]

    assert count == 3