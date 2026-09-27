import pytest

from src.app import create_app, scrape_lock


def fake_analysis():
    return [
        {
            "question": "Test question?",
            "answer": "50.00%"
        }
    ]


@pytest.mark.buttons
def test_update_analysis():
    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis
    )
    client = app.test_client()

    response = client.post("/update-analysis")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}


@pytest.mark.buttons
def test_update_analysis_when_busy():
    scrape_lock.acquire()

    try:
        app = create_app(
            {"TESTING": True},
            analysis_func=fake_analysis
        )
        client = app.test_client()

        response = client.post("/update-analysis")

        assert response.status_code == 409

    finally:
        scrape_lock.release()


@pytest.mark.buttons
def test_pull_data():
    fake_rows = [
        {
            "school": "Test University",
            "program": "Computer Science",
            "degree": "Masters"
        }
    ]

    def fake_scraper():
        return fake_rows

    loaded_rows = []

    def fake_loader(rows):
        loaded_rows.extend(rows)

    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis,
        scraper_func=fake_scraper,
        loader_func=fake_loader
    )

    client = app.test_client()

    response = client.post("/pull-data")

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}
    assert loaded_rows == fake_rows


@pytest.mark.buttons
def test_pull_data_when_busy():
    scrape_lock.acquire()

    try:
        def fake_scraper():
            return []

        app = create_app(
            {"TESTING": True},
            analysis_func=fake_analysis,
            scraper_func=fake_scraper
        )
        client = app.test_client()

        response = client.post("/pull-data")

        assert response.status_code == 409
        assert response.get_json() == {"busy": True}

    finally:
        scrape_lock.release()

@pytest.mark.buttons
def test_pull_data_loader_error():
    def fake_scraper():
        return [
            {
                "school": "Test University",
                "program": "Computer Science",
                "degree": "Masters"
            }
        ]

    def failing_loader(rows):
        raise RuntimeError("Test loader failure")

    app = create_app(
        {"TESTING": True},
        analysis_func=fake_analysis,
        scraper_func=fake_scraper,
        loader_func=failing_loader
    )

    client = app.test_client()

    response = client.post("/pull-data")

    assert response.status_code != 200

@pytest.mark.buttons
def test_run_scraper_success(monkeypatch):
    import src.app as app_module

    class FakeResult:
        returncode = 0

    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *args, **kwargs: FakeResult()
    )

    monkeypatch.setattr(
        app_module,
        "load_scraped_data",
        lambda: 5
    )

    if not app_module.scrape_lock.locked():
        app_module.scrape_lock.acquire()

    app_module.run_scraper()

    assert "5 new applicant(s)" in app_module.scrape_status
    assert app_module.scrape_lock.locked() is False

@pytest.mark.buttons
def test_run_scraper_process_error(monkeypatch):
    import src.app as app_module

    class FakeResult:
        returncode = 1

    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        lambda *args, **kwargs: FakeResult()
    )

    if not app_module.scrape_lock.locked():
        app_module.scrape_lock.acquire()

    app_module.run_scraper()

    assert "stopped with an error" in app_module.scrape_status
    assert app_module.scrape_lock.locked() is False

@pytest.mark.buttons
def test_run_scraper_exception(monkeypatch):
    import src.app as app_module

    def fake_run(*args, **kwargs):
        raise RuntimeError("Test scraper failure")

    monkeypatch.setattr(
        app_module.subprocess,
        "run",
        fake_run
    )

    if not app_module.scrape_lock.locked():
        app_module.scrape_lock.acquire()

    app_module.run_scraper()

    assert "Test scraper failure" in app_module.scrape_status
    assert app_module.scrape_lock.locked() is False

@pytest.mark.buttons
def test_pull_data_normal_mode_starts_thread(monkeypatch):
    import src.app as app_module

    thread_started = {"value": False}

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            thread_started["value"] = True
            # Do NOT actually run the scraper

    monkeypatch.setattr(
        app_module.threading,
        "Thread",
        FakeThread
    )

    app = app_module.create_app(
        {"TESTING": False},
        analysis_func=lambda: []
    )

    client = app.test_client()

    response = client.post("/pull-data")

    assert response.status_code == 202
    assert response.get_json() == {"ok": True}
    assert thread_started["value"] is True

    # The real background thread would eventually release this.
    # Our fake thread never runs, so release it manually.
    if app_module.scrape_lock.locked():
        app_module.scrape_lock.release()