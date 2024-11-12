from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.sql.functions import count

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.hotels.rooms.models import Rooms


class RoomDAO(BaseDAO):
    model = Rooms

    @classmethod
    async def find_all(cls, hotel_id: int, date_from: date, date_to: date):
        """with needed_rooms as (
            select *
            from rooms
            where hotel_id = 1
        ), booked_rooms as (
            select *
            from bookings
            where room_id in (select id from needed_rooms) and (
                (date_from >= '2023-05-15' and date_from < '2023-06-20')
                or
                (date_from <= '2023-05-15' and date_to > '2023-05-15')
            )
        ), total_rooms_cost as (
            select id, price * 15 as total_cost
            from needed_rooms
            group by id, price
        ), leftrooms as (
            select needed_rooms.id, quantity - count(booked_rooms.room_id) as rooms_left
            from needed_rooms
            left join booked_rooms on booked_rooms.room_id = needed_rooms.id
            group by needed_rooms.id, quantity, booked_rooms.room_id
        )

        select *
        from needed_rooms
        join total_rooms_cost on needed_rooms.id = total_rooms_cost.id
        join leftrooms on needed_rooms.id = leftrooms.id"""
        async with async_session_maker() as session:
            needed_rooms = (
                select(Rooms).where(Rooms.hotel_id == hotel_id).cte("needed_rooms")
            )

            booked_rooms = (
                select(Bookings)
                .where(
                    and_(
                        Bookings.room_id == needed_rooms.c.id,
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

            total_rooms_cost = select(
                needed_rooms.c.id,
                (needed_rooms.c.price * (date_to - date_from).days).label("total_cost"),
            ).cte("total_rooms_cost")

            rooms_left = (
                select(
                    needed_rooms.c.id,
                    (needed_rooms.c.quantity - count(booked_rooms.c.room_id)).label(
                        "rooms_left"
                    ),
                )
                .join(
                    booked_rooms,
                    booked_rooms.c.room_id == needed_rooms.c.id,
                    isouter=True,
                )
                .group_by(
                    needed_rooms.c.id, needed_rooms.c.quantity, booked_rooms.c.room_id
                )
                .cte("rooms_left")
            )

            result = (
                select(
                    needed_rooms, total_rooms_cost.c.total_cost, rooms_left.c.rooms_left
                )
                .join(total_rooms_cost, needed_rooms.c.id == total_rooms_cost.c.id)
                .join(rooms_left, needed_rooms.c.id == rooms_left.c.id)
            )

            all_rooms = await session.execute(result)
            return all_rooms.mappings().all()
