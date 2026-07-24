"""Tests for the server-rendered web pages and form flows."""

from conftest import DATE


def test_index_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "ARTIZENT Conference Room Booking" in body
    assert "Boardroom" in body  # seeded room shows in the schedule


def test_book_form_creates_and_shows(client):
    resp = client.post(
        "/book",
        data={
            "room_id": "1",
            "title": "Design review",
            "booked_by": "Dana",
            "date": DATE,
            "start_time": "13:00",
            "end_time": "14:00",
        },
    )
    # Redirects back to the same day's view.
    assert resp.status_code == 302
    assert f"date={DATE}" in resp.headers["Location"]

    page = client.get(f"/?date={DATE}").get_data(as_text=True)
    assert "Design review" in page
    assert "Dana" in page


def test_book_form_overlap_flashes_error(client):
    data = {
        "room_id": "1",
        "title": "First",
        "booked_by": "A",
        "date": DATE,
        "start_time": "10:00",
        "end_time": "11:00",
    }
    client.post("/book", data=data)
    # Overlapping second booking; follow the redirect to read the flash.
    data2 = {**data, "title": "Second", "start_time": "10:30", "end_time": "11:30"}
    resp = client.post("/book", data=data2, follow_redirects=True)
    body = resp.get_data(as_text=True)
    assert "overlaps" in body.lower()
    # Only the first booking should exist.
    assert len(client.get(f"/api/bookings?date={DATE}").get_json()) == 1


def test_cancel_form_removes_booking(client):
    booking_id = client.post(
        "/book",
        data={
            "room_id": "1",
            "title": "Temp",
            "booked_by": "A",
            "date": DATE,
            "start_time": "09:00",
            "end_time": "09:30",
        },
    ) and client.get(f"/api/bookings?date={DATE}").get_json()[0]["id"]

    resp = client.post(f"/cancel/{booking_id}", data={"date": DATE})
    assert resp.status_code == 302
    assert client.get(f"/api/bookings?date={DATE}").get_json() == []
