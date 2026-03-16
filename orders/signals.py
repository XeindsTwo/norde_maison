import threading
import requests
import json
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from shop_config.models import TelegramConfig

from .models import Order


def fmt_price(value, show_zero_as_free=False):
    try:
        amount = float(value)
        if show_zero_as_free and amount == 0:
            return "Бесплатно"
        whole = int(amount)
        frac = round((amount - whole) * 100)
        formatted = f"{whole:,}".replace(",", " ")
        return f"{formatted},{frac:02d} ₽"
    except (TypeError, ValueError):
        return "—"


def get_status_emoji(status):
    status_map = {
        "assembly": "🔄",
        "in_way": "🚚",
        "delivered": "📦",
        "cancelled": "❌"
    }
    return status_map.get(status, "📋")


@receiver(post_save, sender=Order)
def send_order_notifications(sender, instance, created, **kwargs):
    if created and instance.status == 'assembly':
        thread_email = threading.Thread(target=_send_order_email_async, args=(instance,))
        thread_email.daemon = True
        thread_email.start()

        thread_tg = threading.Thread(target=_send_tg_notification_async, args=(instance,))
        thread_tg.daemon = True
        thread_tg.start()
    elif not created and instance.status != 'assembly':
        thread_tg = threading.Thread(target=_send_status_update_async, args=(instance,))
        thread_tg.daemon = True
        thread_tg.start()


def _send_order_email_async(order):
    try:
        html_message = render_to_string(
            "emails/order_confirmation.html",
            {
                "order": order,
                "first_name": order.first_name,
            }
        )

        email = EmailMultiAlternatives(
            subject=f"Заказ #{order.order_number} - Norde Maison",
            body=f"Ваш заказ #{order.order_number} успешно оформлен!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
    except Exception:
        pass


def _send_tg_notification_async(order):
    try:
        config = TelegramConfig.load()
        if not config.bot_token or not config.group_id:
            return

        fio = f"{order.first_name or ''} {order.last_name or ''}".strip()
        if order.middle_name:
            fio += f" {order.middle_name}"

        items_text = ""
        total_items_price = 0

        for item in order.items.all():
            item_price = fmt_price(item.price_snapshot)
            item_subtotal = fmt_price(item.price_snapshot * item.quantity)
            items_text += f"""• <b>{item.product_name}</b>
  {item.color}, {item.size} ×{item.quantity} | {item_price} = {item_subtotal}

"""
            total_items_price += item.price_snapshot * item.quantity

        opts = order._meta
        admin_path = reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[order.pk])
        admin_link = f"{settings.SITE_URL or 'http://127.0.0.1:8000'}{admin_path}"

        extra_parts = []
        if order.delivery_extra:
            extra = order.delivery_extra
            if extra.get("entrance"):
                extra_parts.append(f"Подъезд/дом: {extra['entrance']}")
            if extra.get("floor"):
                extra_parts.append(f"Этаж: {extra['floor']}")
            if extra.get("apartment"):
                extra_parts.append(f"Квартира: {extra['apartment']}")
        extra_display = " · ".join(extra_parts) if extra_parts else "—"

        message = f"""🆕 <b>Новый заказ №{order.order_number}</b>

<b>📋 ТОВАРЫ ({len(order.items.all())} шт)</b>
{items_text}<b>🧾 Итого товары:</b> {fmt_price(total_items_price)}

<b>👤 ФИО:</b> {fio or 'Не указано'}
<b>📞 Телефон:</b> {order.phone or 'Не указан'}
<b>📱 Telegram:</b> {order.telegram or 'Не указан'}

<b>📍 ДОСТАВКА:</b> {order.get_delivery_method_display()}
<b>📦 Страна:</b> {order.country}
<b>🏠 Адрес:</b> {order.address}
<b>📍 Детали адреса:</b> {extra_display}
<b>💰 Доставка:</b> {fmt_price(order.delivery_price, show_zero_as_free=True)}
<b>💳 Итого:</b> {fmt_price(order.total_price)}

<i>Комментарий: {order.comment or 'Нет'}</i>

<a href="{admin_link}">🔗 Посмотреть в админке</a>"""

        url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
        data = {
            "chat_id": config.group_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        requests.post(url, json=data, timeout=10)

    except Exception:
        pass


def _send_status_update_async(order):
    try:
        config = TelegramConfig.load()
        if not config.bot_token or not config.group_id:
            return

        opts = order._meta
        admin_path = reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[order.pk])
        admin_link = f"{settings.SITE_URL or 'http://127.0.0.1:8000'}{admin_path}"

        status_emoji = get_status_emoji(order.status)
        message = f"""📋 <b>Обновление заказа №{order.order_number}</b>

{status_emoji} <b>Статус:</b> <i>{order.get_status_display()}</i>

👤 <b>Клиент:</b> {order.first_name or ''} {order.last_name or ''}
💰 <b>Сумма:</b> {fmt_price(order.total_price)}
📞 <b>Телефон:</b> {order.phone or 'Не указан'}

<a href="{admin_link}">🔗 Перейти в админку</a>"""

        url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
        data = {
            "chat_id": config.group_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        requests.post(url, json=data, timeout=10)

    except Exception:
        pass