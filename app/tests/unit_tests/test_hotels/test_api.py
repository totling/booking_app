import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    "date_from, date_to, status_code",
    [
        ("2023-05-15", "2023-06-10", 200),
        ("2023-05-15", "2023-06-16", 400),
        ("2023-06-15", "2023-06-10", 400),
        ("2023-05-15", "2023-05-15", 400),
    ],
)
async def test_hotels_get(date_from, date_to, status_code, ac: AsyncClient):
    response = await ac.get(
        "/hotels/Алтай", params={"date_from": date_from, "date_to": date_to}
    )

    assert response.status_code == status_code
