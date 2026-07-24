"""SQLite data layer for the Conference Room Booking app.

Uses the stdlib sqlite3 module (no ORM). The database file lives next to this
module as ``bookings.db``.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

# Default to a file next to this module; override with BOOKINGS_DB (used by tests
# to point at a throwaway database).
DB_PATH = os.environ.get("BOOKINGS_DB") or os.path.join(
    os.path.dirname(__file__), "bookings.db"
)

# A few rooms to start with, seeded on first run.
SEED_ROOMS = [
    ("Boardroom", 14, "3rd floor"),
    ("Huddle A", 4, "1st floor"),
    ("Huddle B", 4, "1st floor"),
    ("Training Room", 30, "2nd floor"),
    ("Focus Pod", 2, "1st floor"),
]


@contextmanager
def get_db():
    """Yield a connection, commit on success, and always close it.

    Using ``sqlite3.connect`` as a context manager commits but does *not* close
    the connection — leaking handles/locks under a long-running server. This
    wrapper guarantees the connection is closed. WAL mode improves read/write
    concurrency for the dev server.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if needed and seed rooms on first run."""
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT    NOT NULL UNIQUE,
                capacity INTEGER NOT NULL,
                location TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id    INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
                title      TEXT    NOT NULL,
                booked_by  TEXT    NOT NULL,
                date       TEXT    NOT NULL,   -- YYYY-MM-DD
                start_time TEXT    NOT NULL,   -- HH:MM
                end_time   TEXT    NOT NULL,   -- HH:MM
                created_at TEXT    NOT NULL
            );
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO rooms (name, capacity, location) VALUES (?, ?, ?)",
                SEED_ROOMS,
            )


def list_rooms():
    with get_db() as conn:
        return conn.execute("SELECT * FROM rooms ORDER BY name").fetchall()


def get_room(room_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()


def bookings_for_date(date):
    """All bookings on a date, across rooms, ordered by room then start time."""
    with get_db() as conn:
        return conn.execute(
            """
            SELECT b.*, r.name AS room_name
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
            WHERE b.date = ?
            ORDER BY r.name, b.start_time
            """,
            (date,),
        ).fetchall()


def has_conflict(room_id, date, start_time, end_time, exclude_id=None):
    """True if [start, end) overlaps an existing booking for the room/date."""
    query = (
        "SELECT COUNT(*) FROM bookings "
        "WHERE room_id = ? AND date = ? AND start_time < ? AND end_time > ?"
    )
    params = [room_id, date, end_time, start_time]
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    with get_db() as conn:
        return conn.execute(query, params).fetchone()[0] > 0


def create_booking(room_id, title, booked_by, date, start_time, end_time):
    """Insert a booking. Returns the new row id.

    Raises ValueError with a friendly message on any validation failure or an
    overlap with an existing booking.
    """
    if not get_room(room_id):
        raise ValueError("That room does not exist.")
    if not title.strip():
        raise ValueError("Please give the booking a title.")
    if not booked_by.strip():
        raise ValueError("Please say who the booking is for.")

    _validate_date(date)
    start = _validate_time(start_time, "start time")
    end = _validate_time(end_time, "end time")
    if start >= end:
        raise ValueError("The end time must be after the start time.")

    if has_conflict(room_id, date, start_time, end_time):
        raise ValueError("That time slot overlaps an existing booking for this room.")

    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO bookings
                (room_id, title, booked_by, date, start_time, end_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                room_id,
                title.strip(),
                booked_by.strip(),
                date,
                start_time,
                end_time,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        return cur.lastrowid


def delete_booking(booking_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        return cur.rowcount > 0


def _validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError("Date must be in YYYY-MM-DD format.")


def _validate_time(value, label):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (ValueError, TypeError):
        raise ValueError(f"The {label} must be in HH:MM format.")
