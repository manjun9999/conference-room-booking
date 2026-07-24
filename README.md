# ARTIZENT Conference Room Booking

A small Flask + SQLite app for booking meeting rooms. Pick a date, see each
room's schedule, book a time slot, and cancel bookings. Overlapping bookings for
the same room are rejected.

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000. The SQLite database (`bookings.db`) is created
automatically on first run and seeded with a few rooms.

`python app.py` runs Flask's **development** server — convenient, but
single-threaded and known to drop rapid connections on Windows. Use it for
local development only; for anything else see [Production](#production).

## Production

Run behind [waitress](https://github.com/Pylons/waitress), a production-quality
WSGI server that works well on Windows:

```bash
pip install -r requirements.txt   # includes waitress
python serve.py                   # serves on http://0.0.0.0:8000
```

Override the bind address with `HOST` / `PORT` environment variables.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The suite (`tests/`) uses Flask's test client against a fresh temp database per
test (no network, no dev-server flakiness) and covers the API, validation, the
overlap rules, and the web form/cancel flows.

## Features

- **Rooms** — seeded catalog (name, capacity, location).
- **Bookings** — title, who it's for, date, start/end time.
- **Double-booking prevention** — a new booking that overlaps an existing one
  for the same room and date is rejected with a message.
- **Date view** — browse any day's schedule per room.
- **JSON API** — for scripting/integration (see below).

## JSON API

| Method | Route                    | Purpose                          |
| ------ | ------------------------ | -------------------------------- |
| GET    | `/api/rooms`             | List rooms                       |
| GET    | `/api/bookings?date=`    | Bookings for a date (default today) |
| POST   | `/api/bookings`          | Create a booking (JSON body)     |
| DELETE | `/api/bookings/<id>`     | Cancel a booking                 |

Example:

```bash
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{"room_id":1,"title":"Sprint planning","booked_by":"Alex","date":"2026-07-24","start_time":"10:00","end_time":"11:00"}'
```

## Project structure

```
ConferenceRoomBooking/
├── app.py                Flask app: web routes + JSON API
├── db.py                 SQLite schema, seed data, queries, validation
├── serve.py              Production entrypoint (waitress)
├── requirements.txt      Flask, waitress
├── requirements-dev.txt  + pytest
├── pytest.ini            Pytest config
├── conftest.py           Test fixtures (temp DB + client)
├── tests/
│   ├── test_api.py       JSON API + validation
│   ├── test_overlap.py   Double-booking / overlap rules
│   └── test_web.py       Web pages + form flows
├── templates/
│   ├── base.html         Layout + flash messages
│   └── index.html        Date picker, booking form, per-room schedule
└── static/
    └── style.css         Styling
```

## Notes

- The `secret_key` in `app.py` is a dev placeholder (used for flash messages).
  Set a real secret via environment before deploying.
- Times are stored as `HH:MM` strings and dates as `YYYY-MM-DD`; overlap is
  checked as `start < existing_end AND end > existing_start`.
- No authentication — "booked by" is a free-text field for now.
- Set `BOOKINGS_DB` to point the database at a different file (the test suite
  uses this to isolate each test).
