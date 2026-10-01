"""Central database configuration for Module 5."""

import os

import psycopg
from dotenv import load_dotenv
from sqlalchemy import URL


load_dotenv()


def get_db_settings():
    """Return database connection settings from environment variables."""
    return {
        "host": os.environ["DB_HOST"],
        "port": os.environ["DB_PORT"],
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }


def get_psycopg_connection():
    """Create a psycopg database connection using environment variables."""
    return psycopg.connect(**get_db_settings())


def get_sqlalchemy_url():
    """Create a SQLAlchemy database URL using environment variables."""
    settings = get_db_settings()

    return URL.create(
        drivername="postgresql+psycopg",
        username=settings["user"],
        password=settings["password"],
        host=settings["host"],
        port=int(settings["port"]),
        database=settings["dbname"],
    )
