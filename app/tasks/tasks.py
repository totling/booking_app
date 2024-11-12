import smtplib
from pathlib import Path

from PIL import Image
from pydantic import EmailStr

from app.config import settings
from app.tasks.celery_app import celery_app_var
from app.tasks.email_templates import create_booking_confirmation_template


@celery_app_var.task
def process_pic(
    path: str,
):
    im_path = Path(path)
    img = Image.open(im_path)
    im_resized_1000_500 = img.resize((1000, 500))
    im_resized_200_100 = img.resize((200, 100))
    im_resized_1000_500.save(f"static/images/resized_1000_500_{im_path.name}")
    im_resized_200_100.save(f"static/images/resized_200_100_{im_path.name}")


@celery_app_var.task
def send_booking_confirmation_email(booking: dict, email_to: EmailStr):
    email_to_mock = settings.SMTP_USER
    msg_content = create_booking_confirmation_template(booking, email_to_mock)

    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg_content)
