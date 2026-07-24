"""Tests for the double-booking / overlap logic."""

import pytest

from conftest import DATE, make_booking


@pytest.fixture
def booked(client):
    """A client with one booking already in place: room 1, 10:00–11:00."""
    client.post("/api/bookings", json=make_booking(start_time="10:00", end_time="11:00"))
    return client


@pytest.mark.parametrize(
    "start,end",
    [
        ("10:30", "11:30"),  # overlaps the end
        ("09:30", "10:30"),  # overlaps the start
        ("10:15", "10:45"),  # fully contained
        ("09:30", "11:30"),  # fully contains
        ("10:00", "11:00"),  # exact same slot
    ],
)
def test_overlapping_rejected(booked, start, end):
    resp = booked.post("/api/bookings", json=make_booking(start_time=start, end_time=end))
    assert resp.status_code == 400
    assert "overlap" in resp.get_json()["error"].lower()


@pytest.mark.parametrize(
    "start,end",
    [
        ("11:00", "12:00"),  # starts exactly when the other ends
        ("09:00", "10:00"),  # ends exactly when the other starts
    ],
)
def test_adjacent_allowed(booked, start, end):
    resp = booked.post("/api/bookings", json=make_booking(start_time=start, end_time=end))
    assert resp.status_code == 201


def test_same_time_different_room_allowed(booked):
    resp = booked.post("/api/bookings", json=make_booking(room_id=2, start_time="10:00", end_time="11:00"))
    assert resp.status_code == 201


def test_same_time_different_date_allowed(booked):
    resp = booked.post("/api/bookings", json=make_booking(date="2026-07-25", start_time="10:00", end_time="11:00"))
    assert resp.status_code == 201
