from datetime import date, datetime, timedelta

from fastapi import APIRouter, Query
from fastapi_cache.decorator import cache
from pydantic import parse_obj_as

from app.exceptions import IncorrectInputException
from app.hotels.dao import HotelDAO
from app.hotels.schemas import SHotel, SHotels

router = APIRouter(
    prefix="/hotels",
    tags=["Отели"]
)


@router.get("/{location}")
@cache(expire=30)
async def get_hotels(
    location: str,
    date_from: date = Query(..., description=f"Например, {datetime.now().date()}"),
    date_to: date = Query(..., description=f"Например, {datetime.now().date()}"),
):
    if date_from >= date_to or date_to - date_from > timedelta(days=30):
        raise IncorrectInputException
    if date_to - date_from <= timedelta(days=30):
        hotels = await HotelDAO.find_all(location, date_from, date_to)
        hotels_json = parse_obj_as(list[SHotels], hotels)
        return hotels_json


@router.get("/id/{hotel_id}")
async def get_hotel(hotel_id: int) -> SHotel:
    return await HotelDAO.find_by_id(hotel_id)
