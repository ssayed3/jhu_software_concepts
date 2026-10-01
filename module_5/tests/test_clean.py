import pytest

from src.clean import load_json, save_json, make_key


@pytest.mark.integration
def test_save_and_load_json(tmp_path):
    test_file = tmp_path / "test.json"

    data = {
        "program": "Computer Science",
        "school": "Johns Hopkins University"
    }

    save_json(data, test_file)
    loaded_data = load_json(test_file)

    assert loaded_data == data


@pytest.mark.integration
def test_make_key():
    result = make_key(
        "Computer Science",
        "Johns Hopkins University"
    )

    assert result == "Computer Science|||Johns Hopkins University"

@pytest.mark.integration
def test_load_cache_when_file_exists(tmp_path, monkeypatch):
    import src.clean as clean

    cache_file = tmp_path / "cache.json"

    save_json(
        {"Computer Science|||JHU": {"result": "cleaned"}},
        cache_file
    )

    monkeypatch.setattr(clean, "CACHE_FILE", cache_file)

    result = clean.load_cache()

    assert "Computer Science|||JHU" in result


@pytest.mark.integration
def test_load_cache_when_file_missing(tmp_path, monkeypatch):
    import src.clean as clean

    cache_file = tmp_path / "missing_cache.json"

    monkeypatch.setattr(clean, "CACHE_FILE", cache_file)

    result = clean.load_cache()

    assert result == {}

@pytest.mark.integration
def test_clean_data(tmp_path, monkeypatch):
    import src.clean as clean

    input_file = tmp_path / "applicant_data.json"
    output_file = tmp_path / "llm_extend_applicant_data.json"
    cache_file = tmp_path / "llm_cleaning_cache.json"

    applicants = [
        {
            "program": "Computer Science",
            "school": "Test University"
        },
        {
            "program": "Data Science",
            "school": "Test University"
        }
    ]

    save_json(applicants, input_file)

    monkeypatch.setattr(clean, "INPUT_FILE", input_file)
    monkeypatch.setattr(clean, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(clean, "CACHE_FILE", cache_file)

    def fake_llm(text):
        program, school = text.split(", ", 1)

        return {
            "standardized_program": program,
            "standardized_university": school
        }

    monkeypatch.setattr(clean, "_call_llm", fake_llm)

    clean.clean_data()

    result = load_json(output_file)

    assert len(result) == 2
    assert result[0]["llm-generated-program"] == "Computer Science"
    assert result[0]["llm-generated-university"] == "Test University"

@pytest.mark.integration
def test_clean_data_uses_existing_cache(tmp_path, monkeypatch):
    import src.clean as clean

    input_file = tmp_path / "applicant_data.json"
    output_file = tmp_path / "output.json"
    cache_file = tmp_path / "cache.json"

    applicants = [
        {
            "program": "Computer Science",
            "school": "Test University"
        }
    ]

    cache = {
        "Computer Science|||Test University": {
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "Test University"
        }
    }

    save_json(applicants, input_file)
    save_json(cache, cache_file)

    monkeypatch.setattr(clean, "INPUT_FILE", input_file)
    monkeypatch.setattr(clean, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(clean, "CACHE_FILE", cache_file)

    def fake_llm(text):
        raise AssertionError("LLM should not be called")

    monkeypatch.setattr(clean, "_call_llm", fake_llm)

    clean.clean_data()

    result = load_json(output_file)

    assert len(result) == 1

@pytest.mark.integration
def test_clean_data_prints_progress(tmp_path, monkeypatch, capsys):
    import src.clean as clean

    input_file = tmp_path / "applicant_data.json"
    output_file = tmp_path / "output.json"
    cache_file = tmp_path / "cache.json"

    applicants = [
        {
            "program": f"Program {i}",
            "school": "Test University"
        }
        for i in range(100)
    ]

    save_json(applicants, input_file)

    monkeypatch.setattr(clean, "INPUT_FILE", input_file)
    monkeypatch.setattr(clean, "OUTPUT_FILE", output_file)
    monkeypatch.setattr(clean, "CACHE_FILE", cache_file)

    def fake_llm(text):
        program, school = text.split(", ", 1)
        return {
            "standardized_program": program,
            "standardized_university": school
        }

    monkeypatch.setattr(clean, "_call_llm", fake_llm)

    clean.clean_data()

    captured = capsys.readouterr()

    assert "Progress: 100 of 100 unique pairs" in captured.out

