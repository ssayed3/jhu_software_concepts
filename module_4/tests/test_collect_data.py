import runpy

import pytest
import src.scrape


@pytest.mark.integration
def test_collect_data_main(monkeypatch):
    called = {"value": False}

    def fake_collect_data():
        called["value"] = True

    monkeypatch.setattr(src.scrape, "collect_data", fake_collect_data)

    runpy.run_module("src.collect_data", run_name="__main__")

    assert called["value"] is True
