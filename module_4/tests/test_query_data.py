import pytest

from src import query_data


class FakeCursor:
    def __init__(self, result):
        self.result = result
        self.executed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def execute(self, query, params=None):
        self.executed = True

    def fetchone(self):
        return self.result


class FakeConnection:
    def __init__(self, result):
        self.result = result

    def cursor(self):
        return FakeCursor(self.result)

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
    conn = FakeConnection((47.9234,))
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

    query_data.question_9(conn, original_count=28)

    output = capsys.readouterr().out

    assert "Question 9" in output
    assert "Original-field count: 28" in output
    assert "LLM-generated-field count: 24" in output
    assert "Difference: -4" in output
    assert "normalize variations" in output


@pytest.mark.db
def test_question_9_no_difference(capsys):
    conn = FakeConnection((28,))

    query_data.question_9(conn, original_count=28)

    output = capsys.readouterr().out

    assert "Question 9" in output
    assert "Difference: 0" in output
    assert "same count" in output

@pytest.mark.db
def test_question_10(capsys):
    conn = FakeConnection((15000,))

    query_data.question_10(conn)

    output = capsys.readouterr().out

    assert "Question 10" in output
    assert "15000" in output


@pytest.mark.db
def test_question_11(capsys):
    conn = FakeConnection((3.81,))

    query_data.question_11(conn)

    output = capsys.readouterr().out

    assert "Question 11" in output
    assert "3.81" in output

@pytest.mark.db
def test_get_applicant_by_url_not_found():
    conn = FakeConnection(None)

    result = query_data.get_applicant_by_url(
        conn,
        "https://example.com/not-found"
    )

    assert result is None

@pytest.mark.db
def test_connect_to_database(monkeypatch):
    fake_connection = object()

    def fake_connect(*args, **kwargs):
        assert args[0] == query_data.DATABASE_URL
        return fake_connection

    monkeypatch.setattr(query_data.psycopg, "connect", fake_connect)

    result = query_data.connect_to_database()

    assert result is fake_connection

@pytest.mark.db
def test_main(monkeypatch):
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    fake_conn = FakeConnection()
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

    assert calls == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]