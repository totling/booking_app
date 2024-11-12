from datetime import date

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.functions import coalesce, count

from app.bookings.models import Bookings
from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.exceptions import UserCantDeleteBookingException
from app.hotels.rooms.models import Rooms
from app.logger import logger


class BookingDAO(BaseDAO):
    model = Bookings

    @classmethod
    async def add(
        cls,
        user_id: int,
        room_id: int,
        date_from: date,
        date_to: date,
    ):
        """
        with booked_rooms as (
            select * from bookings
            where room_id = 1
        )
        select rooms.quantity - count(booked_rooms.room_id) as rooms_left from rooms
        left join booked_rooms on booked_rooms.room_id = rooms.id
        where rooms.id = 1
        group by rooms.quantity, booked_rooms.room_id
        """
        try:
            async with async_session_maker() as session:
                booked_rooms = (
                    select(Bookings)
                    .where(
                        Bookings.room_id == room_id,
                    )
                    .cte("booked_rooms")
                )

                get_rooms_left = (
                    select(
                        (Rooms.quantity - coalesce(count(booked_rooms.c.room_id), 0)).label(
                            "rooms_left"
                        )
                    )
                    .select_from(Rooms)
                    .outerjoin(booked_rooms, booked_rooms.c.room_id == Rooms.id)
                    .where(Rooms.id == room_id)
                    .group_by(Rooms.quantity, booked_rooms.c.room_id)
                )

                rooms_left_answ = await session.execute(get_rooms_left)

                rooms_left_var: int = rooms_left_answ.scalar()

                if rooms_left_var > 0:
                    get_price = select(Rooms.price).filter_by(id=room_id)
                    price_answ = await session.execute(get_price)
                    price: int = price_answ.scalar()
                    add_bookings = (
                        insert(Bookings)
                        .values(
                            room_id=room_id,
                            user_id=user_id,
                            date_from=date_from,
                            date_to=date_to,
                            price=price,
                        )
                        .returning(Bookings)
                    )

                    new_booking = await session.execute(add_bookings)
                    await session.commit()
                    return new_booking.scalar()

                else:
                    return None
        except (SQLAlchemyError, Exception) as e:
            if isinstance(e, SQLAlchemyError):
                msg = "Database Exc"
            elif isinstance(e, Exception):
                msg = "Unknown Exc"
            msg += ": Cannot add booking"
            extra = {
                "user_id": user_id,
                "room_id": room_id,
                "date_from": date_from,
                "date_to": date_to,
            }
            logger.error(msg, extra=extra, exc_info=True)

    @classmethod
    async def find_all(cls, user_id: int):
        """with user_bookings as(
            select *
            from bookings
            where bookings.user_id = 3
        ), some_rooms as (
            select rooms.id, image_id, name, description, services
            from rooms
            where rooms.id in (
                select room_id
                from user_bookings
            )
        )

        select *
        from user_bookings
        left join some_rooms on user_bookings.room_id = some_rooms.id
        """
        async with async_session_maker() as session:
            user_bookings = (
                select(Bookings).where(Bookings.user_id == user_id).cte("user_bookings")
            )

            some_rooms = (
                select(
                    Rooms.id,
                    Rooms.image_id,
                    Rooms.name,
                    Rooms.description,
                    Rooms.services,
                )
                .where(Rooms.id.in_(select(user_bookings.c.room_id)))
                .cte("some_rooms")
            )

            query = select(
                user_bookings,
                some_rooms.c.image_id,
                some_rooms.c.name,
                some_rooms.c.description,
                some_rooms.c.services,
            ).join(some_rooms, user_bookings.c.room_id == some_rooms.c.id)

            result = await session.execute(query)

            return result.mappings().all()

    @classmethod
    async def delete(cls, booking_id: int, user_id: int):
        async with async_session_maker() as session:
            booking = select(Bookings.user_id).where(Bookings.id == booking_id)

            booking_user_id_sel = await session.execute(booking)
            booking_user_id = booking_user_id_sel.scalar()

            if not booking_user_id == user_id:
                raise UserCantDeleteBookingException

            query = delete(Bookings).where(Bookings.id == booking_id)

            await session.execute(query)
            await session.commit()
