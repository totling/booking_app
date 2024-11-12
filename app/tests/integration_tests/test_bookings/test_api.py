import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    "room_id, date_from, date_to, booked_rooms, status_code",
    [
        (4, "2030-05-01", "2030-05-15", 3, 200),
        (4, "2030-05-01", "2030-05-15", 4, 200),
        (4, "2030-05-01", "2030-05-15", 5, 200),
        (4, "2030-05-01", "2030-05-15", 6, 200),
        (4, "2030-05-01", "2030-05-15", 7, 200),
        (4, "2030-05-01", "2030-05-15", 8, 200),
        (4, "2030-05-01", "2030-05-15", 9, 200),
        (4, "2030-05-01", "2030-05-15", 10, 200),
        (4, "2030-05-01", "2030-05-15", 10, 409),
        (4, "2030-05-01", "2030-05-15", 10, 409),
    ],
)
async def test_add_and_get_booking(
    room_id,
    date_from,
    date_to,
    booked_rooms,
    status_code,
    authenticated_ac: AsyncClient,
):
    response = await authenticated_ac.post(
        "/bookings",
        params={
            "room_id": room_id,
            "date_from": date_from,
            "date_to": date_to,
        },
    )

    assert response.status_code == status_code

    response = await authenticated_ac.get("/bookings")

    assert len(response.json()) == booked_rooms


@pytest.mark.parametrize(
    "email, password",
    [
        ("test@test.com", "test"),
        ("danik@example.com", "test1"),
    ],
)
async def test_get_and_delete_bookings(email, password, ac: AsyncClient):
    await ac.post("/auth/login", json={"email": email, "password": password})

    response = await ac.get("/bookings")

    assert response.status_code == 200

    for i in response.json():
        await ac.delete(f"/bookings/{i['id']}")

    response = await ac.get("/bookings")

    assert len(response.json()) == 0
