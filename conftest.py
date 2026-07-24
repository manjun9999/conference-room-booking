"""Pytest fixtures.

Point the database at a throwaway location *before* importing the app (its
import runs ``db.init_db()``), then give each test its own fresh, seeded
database via the ``client`` fixture.
"""

import os
import tempfile

# Must be set before importing app/db so the import-time init_db() is harmless.
os.environ["BOOKINGS_DB"] = os.path.join(tempfile.mkdtemp(), "import.db")

import pytest  # noqa: E402

import db  # noqa: E402
from app import app as flask_app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A Flask test client backed by a fresh, seeded database per test."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as c:
        yield c


# A default date used across tests.
DATE = "2026-07-24"


def make_booking(**overrides):
    """Build a valid booking payload, with per-call overrides."""
    payload = {
        "room_id": 1,
        "title": "Sprint planning",
        "booked_by": "Alex",
        "date": DATE,
        "start_time": "10:00",
        "end_time": "11:00",
    }
    payload.update(overrides)
    return payload
