from datetime import date, datetime

from fastapi import APIRouter, Query

from app.hotels.rooms.dao import RoomDAO
from app.hotels.rooms.schemas import SRoom

router = APIRouter(
    prefix="/hotels",
    tags=["Отели"]
)


@router.get("/{hotel_id}/rooms")
async def get_all_rooms(
    hotel_id: int,
    date_from: date = Query(..., description=f"Например, {datetime.now().date()}"),
    date_to: date = Query(..., description=f"Например, {datetime.now().date()}"),
) -> list[SRoom]:
    return await RoomDAO.find_all(hotel_id, date_from, date_to)
