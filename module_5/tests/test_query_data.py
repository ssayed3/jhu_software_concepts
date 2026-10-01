"""Tests for applicant database analysis queries."""

import pytest

from src import query_data


class FakeCursor:
    """Provide a simple fake database cursor for query tests."""

    def __init__(self, result):
        self.result = result
        self.executed = False
        self.query = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def execute(self, query, params=None):
        self.executed = True
        self.query = query
        self.params = params

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result


class FakeConnection:
    """Provide a simple fake database connection for query tests."""

    def __init__(self, result):
        self.result = result
        self.cursor_instance = FakeCursor(result)

    def cursor(self):
        return self.cursor_instance


@pytest.mark.db
def test_question_1(capsys):
    conn = FakeConnection((29576,))

    query_data.question_1(conn)

    output = capsys.readouterr().out

    assert "Question 1" in output
    assert "29576" in output


@pytest.mark.db
def test_question_2(capsys):
    conn = FakeConnection((46.34123,))

    query_data.question_2(conn)

    output = capsys.readouterr().out

    assert "Question 2" in output
    assert "46.34%" in output


@pytest.mark.db
def test_question_3(capsys):
    conn = FakeConnection((3.79, 259.81, 161.53, 8.34))

    query_data.question_3(conn)

    output = capsys.readouterr().out

    assert "3.79" in output
    assert "259.81" in output
    assert "161.53" in output
    assert "8.34" in output


@pytest.mark.db
def test_question_4(capsys):
    conn = FakeConnection((3.79,))

    query_data.question_4(conn)

    output = capsys.readouterr().out

    assert "Question 4" in output
    assert "3.79" in output


@pytest.mark.db
def test_question_5(capsys):
    conn = FakeConnection((47.92,))

    query_data.question_5(conn)

    output = capsys.readouterr().out

    assert "Question 5" in output
    assert "47.92%" in output


@pytest.mark.db
def test_question_6(capsys):
    conn = FakeConnection((3.78,))

    query_data.question_6(conn)

    output = capsys.readouterr().out

    assert "Question 6" in output
    assert "3.78" in output


@pytest.mark.db
def test_question_7(capsys):
    conn = FakeConnection((8,))

    query_data.question_7(conn)

    output = capsys.readouterr().out

    assert "Question 7" in output
    assert "8" in output


@pytest.mark.db
def test_question_8(capsys):
    conn = FakeConnection((28,))

    result = query_data.question_8(conn)

    output = capsys.readouterr().out

    assert "Question 8" in output
    assert "28" in output
    assert result == 28


@pytest.mark.db
def test_question_9_difference(capsys):
    conn = FakeConnection((24,))

    query_data.question_9(conn, 28)

    output = capsys.readouterr().out

    assert "Question 9" in output
    assert "28" in output
    assert "24" in output
    assert "-4" in output
    assert "normalize variations" in output


@pytest.mark.db
def test_question_9_no_difference(capsys):
    conn = FakeConnection((28,))

    query_data.question_9(conn, 28)

    output = capsys.readouterr().out

    assert "Question 9" in output
    assert "28" in output
    assert "same count" in output


@pytest.mark.db
def test_question_10(capsys):
    conn = FakeConnection((100,))

    query_data.question_10(conn)

    output = capsys.readouterr().out

    assert "Question 10" in output
    assert "100" in output


@pytest.mark.db
def test_question_11(capsys):
    conn = FakeConnection((3.85,))

    query_data.question_11(conn)

    output = capsys.readouterr().out

    assert "Question 11" in output
    assert "3.85" in output


def test_connect_to_database(monkeypatch):
    """Verify connect_to_database delegates to the shared DB helper."""
    fake_connection = object()

    monkeypatch.setattr(
        query_data,
        "get_psycopg_connection",
        lambda: fake_connection
    )

    result = query_data.connect_to_database()

    assert result is fake_connection


def test_main(monkeypatch):
    """Verify main runs all applicant analysis questions."""

    class FakeMainConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    fake_conn = FakeMainConnection()
    calls = []

    monkeypatch.setattr(
        query_data,
        "connect_to_database",
        lambda: fake_conn
    )

    for number in range(1, 8):
        monkeypatch.setattr(
            query_data,
            f"question_{number}",
            lambda conn, n=number: calls.append(n)
        )

    def fake_question_8(conn):
        calls.append(8)
        return 28

    def fake_question_9(conn, original_count):
        calls.append(9)
        assert original_count == 28

    monkeypatch.setattr(query_data, "question_8", fake_question_8)
    monkeypatch.setattr(query_data, "question_9", fake_question_9)

    monkeypatch.setattr(
        query_data,
        "question_10",
        lambda conn: calls.append(10)
    )

    monkeypatch.setattr(
        query_data,
        "question_11",
        lambda conn: calls.append(11)
    )

    query_data.main()

    assert calls == list(range(1, 12))


def test_clamp_limit():
    """Verify query limits are restricted to the safe range of 1 to 100."""
    assert query_data.clamp_limit(0) == 1
    assert query_data.clamp_limit(1) == 1
    assert query_data.clamp_limit(50) == 50
    assert query_data.clamp_limit(100) == 100
    assert query_data.clamp_limit(500) == 100


def test_get_applicants_clamps_oversized_limit():
    """Verify oversized query limits are clamped to 100."""
    rows = [
        ("Program A", "Accepted", "Fall 2026", "MS", "url-a")
    ]
    conn = FakeConnection(rows)

    result = query_data.get_applicants(conn, limit=500)

    assert conn.cursor_instance.params == (100,)
    assert "LIMIT %s" in conn.cursor_instance.query.as_string()
    assert result == rows
