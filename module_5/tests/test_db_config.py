"""Tests for centralized database configuration."""

from src import db_config


def test_get_psycopg_connection(monkeypatch):
    """Verify psycopg receives database settings from the environment."""
    fake_connection = object()

    fake_settings = {
        "host": "localhost",
        "port": "5432",
        "dbname": "test_db",
        "user": "test_user",
        "password": "test_password",
    }

    monkeypatch.setattr(
        db_config,
        "get_db_settings",
        lambda: fake_settings
    )

    def fake_connect(**kwargs):
        assert kwargs == fake_settings
        return fake_connection

    monkeypatch.setattr(
        db_config.psycopg,
        "connect",
        fake_connect
    )

    result = db_config.get_psycopg_connection()

    assert result is fake_connection
