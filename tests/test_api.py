"""Tests for the JSON API and validation rules."""

from conftest import DATE, make_booking


def test_rooms_seeded(client):
    resp = client.get("/api/rooms")
    assert resp.status_code == 200
    rooms = resp.get_json()
    assert len(rooms) == 5
    assert {"id", "name", "capacity", "location"} <= set(rooms[0])


def test_create_booking(client):
    resp = client.post("/api/bookings", json=make_booking())
    assert resp.status_code == 201
    assert "id" in resp.get_json()

    listing = client.get(f"/api/bookings?date={DATE}").get_json()
    assert len(listing) == 1
    assert listing[0]["title"] == "Sprint planning"
    assert listing[0]["room_name"] == "Boardroom"


def test_bookings_scoped_by_date(client):
    client.post("/api/bookings", json=make_booking(date="2026-07-24"))
    client.post("/api/bookings", json=make_booking(date="2026-07-25"))

    assert len(client.get("/api/bookings?date=2026-07-24").get_json()) == 1
    assert len(client.get("/api/bookings?date=2026-07-25").get_json()) == 1
    assert client.get("/api/bookings?date=2026-07-26").get_json() == []


def test_delete_booking(client):
    booking_id = client.post("/api/bookings", json=make_booking()).get_json()["id"]
    assert client.delete(f"/api/bookings/{booking_id}").status_code == 200
    assert client.get(f"/api/bookings?date={DATE}").get_json() == []


def test_delete_missing_booking(client):
    assert client.delete("/api/bookings/999999").status_code == 404


def test_validation_errors(client):
    # end before start
    r = client.post("/api/bookings", json=make_booking(start_time="14:00", end_time="13:00"))
    assert r.status_code == 400
    assert "after" in r.get_json()["error"]

    # bad time format
    assert client.post("/api/bookings", json=make_booking(start_time="9am")).status_code == 400

    # missing title
    assert client.post("/api/bookings", json=make_booking(title="  ")).status_code == 400

    # missing booked_by
    assert client.post("/api/bookings", json=make_booking(booked_by="")).status_code == 400

    # nonexistent room
    assert client.post("/api/bookings", json=make_booking(room_id=999)).status_code == 400

    # bad date format
    assert client.post("/api/bookings", json=make_booking(date="24-07-2026")).status_code == 400
