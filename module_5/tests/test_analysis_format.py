import re

import pytest

from src.app import create_app

def fake_analysis():
    return [
        {
            "question": "What percentage of applicants are international?",
            "answer": "46.34%"
        },
        {
            "question": "What percentage of applications were accepted?",
            "answer": "47.92%"
        }
    ]

@pytest.mark.analysis
def test_analysis_format():
    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis
    )
    client = app.test_client()

    response = client.get("/analysis")

    assert response.status_code == 200
    assert b"Answer:" in response.data

    page_text = response.get_data(as_text=True)

    percentages = re.findall(r"\d+\.\d{2}%", page_text)

    assert "46.34%" in percentages
    assert "47.92%" in percentages