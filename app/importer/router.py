import pandas as pd

from ast import literal_eval
from fastapi import APIRouter, UploadFile, status, Depends

from app.bookings.dao import BookingDAO
from app.exceptions import IncorrectInputException
from app.hotels.dao import HotelDAO
from app.hotels.rooms.dao import RoomDAO
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user
from app.users.models import Users

router = APIRouter(
    prefix="/import",
    tags=["Импорт значений"],
)


@router.post("/{table_name}")
async def import_data(table_name: str, file: UploadFile, user: Users = Depends(get_current_user)):
    data = pd.read_csv(file.file, sep=";", encoding="utf-8")

    if table_name == "bookings":
        for row in data.itertuples(index=False):
            row_dict = row._asdict()
            await BookingDAO.add(**row_dict)
    elif table_name == "hotels":
        for row in data.itertuples(index=False):
            row_dict = row._asdict()
            row_dict["services"] = literal_eval(row_dict["services"])
            await HotelDAO.add(**row_dict)
    elif table_name == "rooms":
        for row in data.itertuples(index=False):
            row_dict = row._asdict()
            row_dict["services"] = literal_eval(row_dict["services"])
            await RoomDAO.add(**row_dict)
    elif table_name == "users":
        for row in data.itertuples(index=False):
            row_dict = row._asdict()
            await UsersDAO.add(**row_dict)
    else:
        raise IncorrectInputException

    return status.HTTP_201_CREATED
