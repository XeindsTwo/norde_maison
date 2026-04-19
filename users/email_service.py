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


def send_activation_email(user, activation_token):
    confirm_url = f"{settings.SITE_URL}/api/auth/confirm/{activation_token}/"
    html_body = render_to_string(
        "users/welcome_email.html",
        {
            "first_name": user.first_name,
            "confirm_url": confirm_url,
        },
    )
    _send_email_with_resend(
        to_email=user.email,
        subject="Подтверждение регистрации",
        text_body=f"Подтвердите email: {confirm_url}",
        html_body=html_body,
    )


def send_password_reset_email(user, token):
    reset_url = f"{settings.SITE_URL_CLIENT}/?reset_token={token}"
    html_body = render_to_string(
        "users/password_reset.html",
        {
            "first_name": user.first_name,
            "reset_url": reset_url,
        },
    )
    _send_email_with_resend(
        to_email=user.email,
        subject="Сброс пароля — Norde Maison",
        text_body="Перейдите по ссылке для смены пароля.",
        html_body=html_body,
    )


def send_password_changed_email(user):
    html_body = render_to_string(
        "users/password_changed.html",
        {
            "first_name": user.first_name,
        },
    )
    _send_email_with_resend(
        to_email=user.email,
        subject="Пароль успешно изменён",
        text_body="Пароль был изменён",
        html_body=html_body,
    )
