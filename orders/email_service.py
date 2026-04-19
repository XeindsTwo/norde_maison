from django.conf import settings
from django.template.loader import render_to_string
import resend


def _send_email_with_resend(*, to_email: str, subject: str, text_body: str, html_body: str):
    api_key = settings.RESEND_API_KEY
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")

    resend.api_key = api_key
    resend.Emails.send(
        {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": text_body,
            "html": html_body,
        }
    )


def send_order_confirmation_email(order):
    html_body = render_to_string(
        "emails/order_confirmation.html",
        {"order": order, "first_name": order.first_name},
    )
    _send_email_with_resend(
        to_email=order.user.email,
        subject=f"Заказ #{order.order_number} - Norde Maison",
        text_body=f"Ваш заказ #{order.order_number} успешно оформлен!",
        html_body=html_body,
    )


def send_order_status_email(order, status: str):
    if status == "in_way":
        profile_url = f"{settings.SITE_URL_CLIENT}/profile/"
    elif status == "delivered":
        profile_url = f"{settings.SITE_URL_CLIENT}/"
    elif status == "cancelled":
        profile_url = f"{settings.SITE_URL_CLIENT}/profile/"
    else:
        return

    html_body = render_to_string(
        "emails/order_status_update.html",
        {"order": order, "status": status, "profile_url": profile_url},
    )

    status_display = order.get_status_display()
    _send_email_with_resend(
        to_email=order.user.email,
        subject=f"Заказ #{order.order_number} - {status_display}",
        text_body=f"Ваш заказ #{order.order_number} обновлён до статуса '{status_display}'",
        html_body=html_body,
    )
