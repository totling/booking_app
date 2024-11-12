from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.sql import functions as func
from sqlalchemy.sql.functions import count

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.hotels.models import Hotels
from app.hotels.rooms.models import Rooms


class HotelDAO(BaseDAO):
    model = Hotels

    @classmethod
    async def find_all(cls, location: str, date_from: date, date_to: date):
        """
        with hotel_rooms as (
            select * from rooms
            where hotel_id in
            (select id from hotels where location like '%Алтай%')
        ), booked_rooms as (
            select * from bookings
            where room_id in (select id from hotel_rooms) and
            (date_from >= '2023-05-15' and date_from < '2023-06-20') or
            (date_from <= '2023-05-15' and date_to > '2023-05-15')
        ), available_rooms as (
            select hotel_id, hotel_rooms.quantity - count(booked_rooms.room_id) as rooms_left from hotel_rooms
            left join booked_rooms on booked_rooms.room_id = hotel_rooms.id
            group by hotel_id, hotel_rooms.quantity, booked_rooms.room_id
        )

        select * from hotels
        join
        (select hotel_id, sum(rooms_left) as rooms_left from available_rooms group by hotel_id) as available_rooms
        on available_rooms.hotel_id = hotels.id
        """
        async with async_session_maker() as session:
            hotel_rooms = (
                select(Rooms)
                .where(
                    Rooms.hotel_id.in_(
                        select(Hotels.id).where(Hotels.location.like(f"%{location}%"))
                    )
                )
                .cte("hotel_rooms")
            )

            booked_rooms = (
                select(Bookings)
                .where(
                    and_(
                        Bookings.room_id == hotel_rooms.c.id,
                        or_(
                            and_(
                                Bookings.date_from >= date_from,
                                Bookings.date_from < date_to,
                            ),
                            and_(Bookings.date_from <= date_from, date_to > date_from),
                        ),
                    )
                )
                .cte("booked_rooms")
            )

            available_rooms = (
                select(
                    hotel_rooms.c.hotel_id,
                    (hotel_rooms.c.quantity - count(booked_rooms.c.room_id)).label(
                        "rooms_left"
                    ),
                )
                .select_from(hotel_rooms)
                .outerjoin(booked_rooms, booked_rooms.c.room_id == hotel_rooms.c.id)
                .group_by(
                    hotel_rooms.c.hotel_id,
                    hotel_rooms.c.quantity,
                    booked_rooms.c.room_id,
                )
                .cte("available_rooms")
            )

            available_rooms_subquery = (
                select(
                    available_rooms.c.hotel_id,
                    func.sum(available_rooms.c.rooms_left).label("rooms_left"),
                ).group_by(available_rooms.c.hotel_id)
            ).cte("available_rooms_subquery")

            get_all_hotels = (
                select(Hotels, available_rooms_subquery.c.rooms_left)
                .select_from(Hotels)
                .join(
                    available_rooms_subquery,
                    available_rooms_subquery.c.hotel_id == Hotels.id,
                )
                .where(available_rooms_subquery.c.rooms_left > 0)
            )

            all_hotels = await session.execute(get_all_hotels)

            result = []
            for row in all_hotels.mappings().all():
                hotel_data = {**row["Hotels"].__dict__}
                hotel_data.pop("_sa_instance_state", None)
                hotel_data["rooms_left"] = row["rooms_left"]
                result.append(hotel_data)

            return result
