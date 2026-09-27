import pytest

from src import orm_queries


class FakeSession:
    def __init__(self, results):
        self.results = iter(results)

    def scalar(self, statement):
        return next(self.results)


@pytest.mark.db
def test_question_1(capsys):
    session = FakeSession([29576])

    orm_queries.question_1(session)

    output = capsys.readouterr().out

    assert "Question 1" in output
    assert "29576" in output


@pytest.mark.db
def test_question_4(capsys):
    session = FakeSession([3.79])

    orm_queries.question_4(session)

    output = capsys.readouterr().out

    assert "Question 4" in output
    assert "3.79" in output

@pytest.mark.db
def test_question_5(capsys):
    # question_5 calls session.scalar() twice:
    # total applications = 100, accepted = 48
    session = FakeSession([100, 48])

    orm_queries.question_5(session)

    output = capsys.readouterr().out

    assert "Question 5" in output
    assert "48.00%" in output


@pytest.mark.db
def test_question_5_zero_total(capsys):
    # Covers the "if total else 0" branch
    session = FakeSession([0, 0])

    orm_queries.question_5(session)

    output = capsys.readouterr().out

    assert "0.00%" in output


@pytest.mark.db
def test_question_8(capsys):
    session = FakeSession([28])

    result = orm_queries.question_8(session)

    output = capsys.readouterr().out

    assert "Question 8" in output
    assert "28" in output
    assert result == 28


@pytest.mark.db
def test_question_9_difference(capsys):
    session = FakeSession([24])

    orm_queries.question_9(session, original_count=28)

    output = capsys.readouterr().out

    assert "Original-field count: 28" in output
    assert "LLM-generated-field count: 24" in output
    assert "Difference: -4" in output
    assert "normalize" in output


@pytest.mark.db
def test_question_9_no_difference(capsys):
    session = FakeSession([28])

    orm_queries.question_9(session, original_count=28)

    output = capsys.readouterr().out

    assert "Difference: 0" in output
    assert "same count" in output


@pytest.mark.db
def test_question_10(capsys):
    session = FakeSession([15000])

    orm_queries.question_10(session)

    output = capsys.readouterr().out

    assert "Question 10" in output
    assert "15000" in output

@pytest.mark.db
def test_main(monkeypatch):
    calls = []

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

    monkeypatch.setattr(
        orm_queries,
        "SessionLocal",
        lambda: FakeSession()
    )

    monkeypatch.setattr(
        orm_queries,
        "question_1",
        lambda session: calls.append(1)
    )
    monkeypatch.setattr(
        orm_queries,
        "question_4",
        lambda session: calls.append(4)
    )
    monkeypatch.setattr(
        orm_queries,
        "question_5",
        lambda session: calls.append(5)
    )

    def fake_question_8(session):
        calls.append(8)
        return 28

    def fake_question_9(session, original_count):
        calls.append(9)
        assert original_count == 28

    monkeypatch.setattr(orm_queries, "question_8", fake_question_8)
    monkeypatch.setattr(orm_queries, "question_9", fake_question_9)
    monkeypatch.setattr(
        orm_queries,
        "question_10",
        lambda session: calls.append(10)
    )

    orm_queries.main()

    assert calls == [1, 4, 5, 8, 9, 10]