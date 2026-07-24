"""Conference Room Booking — a small Flask + SQLite app.

Server-rendered UI for booking meeting rooms, with double-booking prevention,
plus a small JSON API under /api.
"""

from datetime import date as date_cls

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

import db

app = Flask(__name__)
# Dev-only secret for flash messages. Set a real one via env in production.
app.secret_key = "dev-secret-change-me"

db.init_db()


def _today():
    return date_cls.today().isoformat()


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    selected_date = request.args.get("date") or _today()
    rooms = db.list_rooms()

    # Group the day's bookings by room for easy rendering.
    bookings = db.bookings_for_date(selected_date)
    by_room = {room["id"]: [] for room in rooms}
    for b in bookings:
        by_room.setdefault(b["room_id"], []).append(b)

    return render_template(
        "index.html",
        rooms=rooms,
        bookings_by_room=by_room,
        selected_date=selected_date,
        today=_today(),
    )


@app.post("/book")
def book():
    selected_date = request.form.get("date") or _today()
    try:
        db.create_booking(
            room_id=int(request.form.get("room_id", 0)),
            title=request.form.get("title", ""),
            booked_by=request.form.get("booked_by", ""),
            date=selected_date,
            start_time=request.form.get("start_time", ""),
            end_time=request.form.get("end_time", ""),
        )
        flash("Booking confirmed.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("index", date=selected_date))


@app.post("/cancel/<int:booking_id>")
def cancel(booking_id):
    selected_date = request.form.get("date") or _today()
    if db.delete_booking(booking_id):
        flash("Booking cancelled.", "success")
    else:
        flash("That booking no longer exists.", "error")
    return redirect(url_for("index", date=selected_date))


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------

@app.get("/api/rooms")
def api_rooms():
    return jsonify([dict(r) for r in db.list_rooms()])


@app.get("/api/bookings")
def api_bookings():
    selected_date = request.args.get("date") or _today()
    return jsonify([dict(b) for b in db.bookings_for_date(selected_date)])


@app.post("/api/bookings")
def api_create_booking():
    data = request.get_json(silent=True) or {}
    try:
        booking_id = db.create_booking(
            room_id=int(data.get("room_id", 0)),
            title=data.get("title", ""),
            booked_by=data.get("booked_by", ""),
            date=data.get("date", _today()),
            start_time=data.get("start_time", ""),
            end_time=data.get("end_time", ""),
        )
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"id": booking_id}), 201


@app.delete("/api/bookings/<int:booking_id>")
def api_delete_booking(booking_id):
    if db.delete_booking(booking_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Booking not found"}), 404


if __name__ == "__main__":
    # threaded=True so rapid back-to-back requests aren't serialized/dropped.
    app.run(debug=True, port=5000, threaded=True)
