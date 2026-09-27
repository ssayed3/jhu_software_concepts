import pytest

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Applicant, Base
from src.load_data import load_applicants
from src.query_data import get_applicant_by_url

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    yield session

    session.close()
    engine.dispose()

@pytest.mark.db
def test_insert_applicant(db_session):
    applicant = Applicant(
        program="Computer Science",
        status="Accepted",
        term="Fall 2026",
        degree="Masters",
        url="https://example.com/test-applicant"
    )

    db_session.add(applicant)
    db_session.commit()

    saved_applicant = db_session.query(Applicant).first()

    assert saved_applicant is not None
    assert saved_applicant.program == "Computer Science"
    assert saved_applicant.status == "Accepted"

@pytest.mark.db
def test_required_fields_not_null(db_session):
    applicant = Applicant(
        program="Data Science",
        status="Accepted",
        term="Fall 2026",
        degree="Masters",
        url="https://example.com/applicant-2"
    )

    db_session.add(applicant)
    db_session.commit()

    saved_applicant = db_session.query(Applicant).first()

    assert saved_applicant.program is not None
    assert saved_applicant.status is not None
    assert saved_applicant.term is not None
    assert saved_applicant.degree is not None
    assert saved_applicant.url is not None

@pytest.mark.db
def test_load_applicants_is_idempotent(tmp_path):
    data_file = tmp_path / "test_applicants.json"

    data_file.write_text(
        """
        [
            {
                "school": "Test University",
                "program": "Computer Science",
                "applicant_url": "https://example.com/applicant-1"
            }
        ]
        """,
        encoding="utf-8"
    )

    seen_urls = set()

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def execute(self, query, values):
            url = values[3]

            if url in seen_urls:
                self.rowcount = 0
            else:
                seen_urls.add(url)
                self.rowcount = 1

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    conn = FakeConnection()

    first_insert = load_applicants(conn, data_file=data_file)
    second_insert = load_applicants(conn, data_file=data_file)

    assert first_insert == 1
    assert second_insert == 0
    assert len(seen_urls) == 1

@pytest.mark.db
def test_query_returns_dict_with_expected_keys():
    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def execute(self, query, values):
            pass

        def fetchone(self):
            return (
                "Test University, Computer Science",
                "Accepted",
                "Fall 2026",
                "Masters",
                "https://example.com/applicant-1"
            )

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    conn = FakeConnection()

    result = get_applicant_by_url(
        conn,
        "https://example.com/applicant-1"
    )

    assert isinstance(result, dict)
    assert set(result.keys()) == {
        "program",
        "status",
        "term",
        "degree",
        "url"
    }

@pytest.mark.db
def test_parse_date():
    from src.load_data import parse_date

    assert str(parse_date("Sep 26, 2026")) == "2026-09-26"
    assert parse_date("") is None
    assert parse_date("not a date") is None


@pytest.mark.db
def test_parse_number():
    from src.load_data import parse_number

    assert parse_number("3.79") == 3.79
    assert parse_number(161) == 161.0
    assert parse_number("") is None
    assert parse_number(None) is None
    assert parse_number("not a number") is None


@pytest.mark.db
def test_create_table():
    from src.load_data import create_table

    executed = {"value": False}

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def execute(self, query):
            executed["value"] = True
            assert "CREATE TABLE IF NOT EXISTS applicants" in query

    class FakeConnection:
        def cursor(self):
            return FakeCursor()

    create_table(FakeConnection())

    assert executed["value"] is True

@pytest.mark.db
def test_load_scraped_data(monkeypatch):
    import src.load_data as load_data

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def commit(self):
            self.committed = True

    fake_conn = FakeConnection()
    fake_conn.committed = False

    def fake_connect(*args, **kwargs):
        assert args[0] == load_data.DATABASE_URL
        return fake_conn

    monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)
    monkeypatch.setattr(load_data, "create_table", lambda conn: None)
    monkeypatch.setattr(
        load_data,
        "load_applicants",
        lambda conn, data_file: 5
    )

    result = load_data.load_scraped_data()

    assert result == 5
    assert fake_conn.committed is True

@pytest.mark.db
def test_load_data_main(monkeypatch, capsys):
    import src.load_data as load_data

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def commit(self):
            self.committed = True

    fake_conn = FakeConnection()
    fake_conn.committed = False

    def fake_connect(*args, **kwargs):
        assert args[0] == load_data.DATABASE_URL
        return fake_conn

    monkeypatch.setattr(load_data.psycopg, "connect", fake_connect)
    monkeypatch.setattr(load_data, "create_table", lambda conn: None)
    monkeypatch.setattr(
        load_data,
        "load_applicants",
        lambda conn, data_file: 5
    )

    load_data.main()

    captured = capsys.readouterr()

    assert fake_conn.committed is True
    assert "New applicants inserted: 5" in captured.out
    assert "Data loading complete." in captured.out

@pytest.mark.db
def test_overlapping_data_is_idempotent(tmp_path):
    import json
    import src.load_data as load_data

    class FakeCursor:
        def __init__(self):
            self.urls = set()
            self.rowcount = 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def execute(self, query, values):
            url = values[3]

            if url in self.urls:
                self.rowcount = 0
            else:
                self.urls.add(url)
                self.rowcount = 1

    class FakeConnection:
        def __init__(self):
            self.cursor_instance = FakeCursor()

        def cursor(self):
            return self.cursor_instance

    first_pull = [
        {
            "school": "University A",
            "program": "Computer Science",
            "applicant_url": "https://example.com/a"
        },
        {
            "school": "University B",
            "program": "Data Science",
            "applicant_url": "https://example.com/b"
        }
    ]

    second_pull = [
        {
            "school": "University A",
            "program": "Computer Science",
            "applicant_url": "https://example.com/a"
        },
        {
            "school": "University C",
            "program": "Artificial Intelligence",
            "applicant_url": "https://example.com/c"
        }
    ]

    first_file = tmp_path / "first_pull.json"
    second_file = tmp_path / "second_pull.json"

    first_file.write_text(json.dumps(first_pull))
    second_file.write_text(json.dumps(second_pull))

    conn = FakeConnection()

    first_inserted = load_data.load_applicants(conn, first_file)
    second_inserted = load_data.load_applicants(conn, second_file)

    assert first_inserted == 2
    assert second_inserted == 1
    assert len(conn.cursor_instance.urls) == 3

@pytest.mark.db
def test_real_postgresql_insert_and_idempotency(tmp_path):
    import json
    import psycopg
    import src.load_data as load_data

    test_database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://sayedsayed@/module4_test_db"
    )

    applicants = [
        {
            "school": "Test University",
            "program": "Computer Science",
            "applicant_url": "https://example.com/postgres-test-1",
            "status": "Accepted",
            "degree": "Masters"
        },
        {
            "school": "Example University",
            "program": "Artificial Intelligence",
            "applicant_url": "https://example.com/postgres-test-2",
            "status": "Rejected",
            "degree": "PhD"
        }
    ]

    data_file = tmp_path / "postgres_test.json"
    data_file.write_text(json.dumps(applicants))

    with psycopg.connect(test_database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS applicants;")
        conn.commit()

        load_data.create_table(conn)

        first_inserted = load_data.load_applicants(conn, data_file)
        conn.commit()

        second_inserted = load_data.load_applicants(conn, data_file)
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            count = cur.fetchone()[0]

            cur.execute("""
                SELECT program, url, status, degree
                FROM applicants
                ORDER BY url;
            """)
            rows = cur.fetchall()

    assert first_inserted == 2
    assert second_inserted == 0
    assert count == 2

    assert len(rows) == 2

    for row in rows:
        assert row[0] is not None  # program
        assert row[1] is not None  # url
        assert row[2] is not None  # status
        assert row[3] is not None  # degree