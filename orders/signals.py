import threading
import requests
import time
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from shop_config.models import TelegramConfig
from .models import Order, OrderStatus
from .utils.yookassa import check_payment_status


def fmt_price(value, show_zero_as_free=False):
    try:
        amount = float(value)
        if show_zero_as_free and amount == 0:
            return "Бесплатно"
        whole = int(amount)
        frac = round((amount - whole) * 100)
        formatted = f"{whole:,}".replace(",", " ")
        return f"{formatted},{frac:02d} ₽"
    except:
        return "—"


def get_status_emoji(status):
    return {"assembly": "🔄", "in_way": "🚚", "delivered": "📦", "cancelled": "❌"}.get(status, "📋")


def _send_order_email_async(order):
    try:
        html = render_to_string("emails/order_confirmation.html", {"order": order, "first_name": order.first_name})
        email = EmailMultiAlternatives(
            subject=f"Заказ #{order.order_number} - Norde Maison",
            body=f"Ваш заказ #{order.order_number} успешно оформлен!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email]
        )
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=False)
    except:
        pass


def _send_status_email_async(order, status):
    try:
        if status == "in_way":
            profile_url = f"{settings.SITE_URL_CLIENT}/profile/"
        elif status == "delivered":
            profile_url = f"{settings.SITE_URL_CLIENT}/"
        elif status == "cancelled":
            profile_url = f"{settings.SITE_URL_CLIENT}/profile/"
        else:
            return
        html = render_to_string("emails/order_status_update.html",
                                {"order": order, "status": status, "profile_url": profile_url})
        subject = f"Заказ #{order.order_number} - {order.get_status_display()}"
        body = f"Ваш заказ #{order.order_number} обновлён до статуса '{order.get_status_display()}'"
        email = EmailMultiAlternatives(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL,
                                       to=[order.user.email])
        email.attach_alternative(html, "text/html")
        email.send(fail_silently=True)
    except:
        pass


def _send_tg_notification_async(order):
    try:
        config = TelegramConfig.load()
        if not config.bot_token or not config.group_id:
            return
        fio = " ".join(filter(None, [order.first_name, order.last_name, order.middle_name]))
        items_text = ""
        total_items_price = 0
        for item in order.items.all():
            price = fmt_price(item.price_snapshot)
            subtotal = fmt_price(item.price_snapshot * item.quantity)
            items_text += f"• <b>{item.product_name}</b>\n{item.color}, {item.size} ×{item.quantity} | {price} = {subtotal}\n\n"
            total_items_price += item.price_snapshot * item.quantity
        opts = order._meta
        admin_link = f"{settings.SITE_URL or 'http://127.0.0.1:8000'}{reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[order.pk])}"
        extra = []
        if order.delivery_extra:
            if order.delivery_extra.get("entrance"): extra.append(f"Подъезд/дом: {order.delivery_extra['entrance']}")
            if order.delivery_extra.get("floor"): extra.append(f"Этаж: {order.delivery_extra['floor']}")
            if order.delivery_extra.get("apartment"): extra.append(f"Квартира: {order.delivery_extra['apartment']}")
        extra_display = " · ".join(extra) if extra else "—"
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
        requests.post(f"https://api.telegram.org/bot{config.bot_token}/sendMessage",
                      json={"chat_id": config.group_id, "text": message, "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=10)
    except:
        pass


def _send_status_update_async(order):
    try:
        config = TelegramConfig.load()
        if not config.bot_token or not config.group_id:
            return
        opts = order._meta
        admin_link = f"{settings.SITE_URL or 'http://127.0.0.1:8000'}{reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[order.pk])}"
        status_emoji = get_status_emoji(order.status)
        message = f"""📋 <b>Обновление заказа №{order.order_number}</b>

{status_emoji} <b>Статус:</b> <i>{order.get_status_display()}</i>

👤 <b>Клиент:</b> {order.first_name or ''} {order.last_name or ''}
💰 <b>Сумма:</b> {fmt_price(order.total_price)}
📞 <b>Телефон:</b> {order.phone or 'Не указан'}

<a href="{admin_link}">🔗 Перейти в админку</a>"""
        requests.post(f"https://api.telegram.org/bot{config.bot_token}/sendMessage",
                      json={"chat_id": config.group_id, "text": message, "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=10)
    except:
        pass


def _send_pending_tg_async(order):
    try:
        config = TelegramConfig.load()
        if not config.bot_token or not config.group_id:
            return
        opts = order._meta
        admin_link = f"{settings.SITE_URL or 'http://127.0.0.1:8000'}{reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[order.pk])}"
        message = f"""⏳ <b>Ожидает оплаты #{order.order_number}</b>

💰 <b>Сумма:</b> {fmt_price(order.total_price)}
👤 <b>Клиент:</b> {getattr(order.user, 'username', 'Гость')}
📞 <b>Телефон:</b> {order.phone or 'Не указан'}

<a href="{admin_link}">🔗 Админка заказа</a>"""
        requests.post(f"https://api.telegram.org/bot{config.bot_token}/sendMessage",
                      json={"chat_id": config.group_id, "text": message, "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=10)
    except:
        pass


@receiver(post_save, sender=Order)
def order_status_change(sender, instance, created, **kwargs):
    if created:
        if instance.status == OrderStatus.PENDING and not instance.payment_id:
            t = threading.Thread(target=_send_pending_tg_async, args=(instance,))
            t.daemon = True
            t.start()
        elif instance.payment_id and instance.status == OrderStatus.ASSEMBLY:
            t_email = threading.Thread(target=_send_order_email_async, args=(instance,))
            t_email.daemon = True
            t_email.start()
            t_tg = threading.Thread(target=_send_tg_notification_async, args=(instance,))
            t_tg.daemon = True
            t_tg.start()
            instance.notified = True
            instance.save(update_fields=["notified"])
        return

    if instance.status != OrderStatus.PENDING and not getattr(instance, "notified", False):
        t_email = threading.Thread(target=_send_status_email_async, args=(instance, instance.status))
        t_email.daemon = True
        t_email.start()
        t_tg = threading.Thread(target=_send_status_update_async, args=(instance,))
        t_tg.daemon = True
        t_tg.start()
        instance.notified = True
        instance.save(update_fields=["notified"])


def check_pending_orders_periodically():
    def run():
        while True:
            try:
                pending_orders = Order.objects.filter(status=OrderStatus.PENDING)
                for order in pending_orders:
                    if order.payment_id and check_payment_status(order.payment_id):
                        order.status = OrderStatus.ASSEMBLY
                        order.save(update_fields=['status'])
                    elif order.created_at < timezone.now() - timedelta(minutes=10):
                        for item in order.items.all():
                            item.variant.stock += item.quantity
                            item.variant.save()
                        order.status = OrderStatus.CANCELLED
                        order.save(update_fields=['status'])
            except:
                pass
            time.sleep(60)

    threading.Thread(target=run, daemon=True).start()
