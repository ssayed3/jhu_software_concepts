import pytest
from src.app import create_app

def fake_analysis():
    return [
        {
            "question": "Test question?",
            "answer": "50.00%"
        }
    ]

@pytest.mark.web
def test_analysis_page():
    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis
    )
    client = app.test_client()
    response = client.get("/analysis")

    assert response.status_code == 200
    assert b"Pull Data" in response.data
    assert b"Update Analysis" in response.data
    assert b"Analysis" in response.data
    assert b"Answer:" in response.data

@pytest.mark.web
def test_get_analysis_results(monkeypatch):
    import src.app as app_module

    class FakeExecuteResult:
        def one(self):
            return (3.79, 259.81, 161.53, 8.34)

    class FakeSession:
        def __init__(self):
            self.scalar_values = iter([
                29576,   # q1
                100,     # total classified
                46,      # international
                3.79,    # q4
                100,     # Fall 2025 total
                48,      # Fall 2025 accepted
                3.78,    # q6
                8,       # q7
                28,      # q8
                24,      # q9 LLM
                15000,   # q10
                3.81     # q11
            ])

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def scalar(self, statement):
            return next(self.scalar_values)

        def execute(self, statement):
            return FakeExecuteResult()

    monkeypatch.setattr(
        app_module,
        "SessionLocal",
        lambda: FakeSession()
    )

    results = app_module.get_analysis_results()

    assert len(results) == 11

    assert results[0]["answer"] == "29,576"
    assert results[1]["answer"] == "46.00%"
    assert "GPA: 3.79" in results[2]["answer"]
    assert results[3]["answer"] == "3.79"
    assert results[4]["answer"] == "48.00%"
    assert results[5]["answer"] == "3.78"
    assert results[6]["answer"] == "8"
    assert results[7]["answer"] == "28"
    assert "Difference: -4" in results[8]["answer"]
    assert results[9]["answer"] == "15,000"
    assert results[10]["answer"] == "3.81"
