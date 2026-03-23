import os
import requests
import threading
from django.conf import settings
from django.urls import reverse
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Product, ProductImage, SubCategory, ProductVariant
from shop_config.models import TelegramConfig


def safe_delete_file(file_field):
    if file_field and file_field.path and os.path.exists(file_field.path):
        try:
            os.remove(file_field.path)
        except Exception:
            pass


def send_low_stock_tg_async(product, variant):
    try:
        config = TelegramConfig.load()
        if not config.bot_token or not config.group_id:
            return

        product_admin_url = f"{settings.SITE_URL or 'http://127.0.0.1:8000'}{reverse('admin:catalog_product_change', args=[product.id])}"

        if variant.stock == 0:
            emoji = "❗️"
            status = "Товар закончился на складе"
            stock_line = ""
        else:
            emoji = "⚠️"
            status = f"Низкий остаток на складе ({variant.stock} шт)"
            stock_line = f"\n📊 Остаток: <b>{variant.stock}</b>"

        message = f"""{emoji} {status}

📋 <b>Товар: {product.name}</b>
🎨 Цвет: {variant.color_name}
📏 Размер одежды: {variant.size}{stock_line}

<a href="{product_admin_url}">🔗 Дозаказать товар</a>"""

        requests.post(
            f"https://api.telegram.org/bot{config.bot_token}/sendMessage",
            json={
                "chat_id": config.group_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except:
        pass


@receiver(post_delete, sender=Product)
def delete_product_files(sender, instance, **kwargs):
    safe_delete_file(instance.main_image)
    for img in instance.images.all():
        safe_delete_file(img.image)


@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    safe_delete_file(instance.image)


@receiver(post_delete, sender=SubCategory)
def delete_subcategory_related(sender, instance, **kwargs):
    instance.products.all().delete()
    safe_delete_file(instance.cover_image)


@receiver(post_save, sender=ProductVariant)
def notify_low_stock(sender, instance, **kwargs):
    if instance.stock > 2:
        return

    thread = threading.Thread(
        target=send_low_stock_tg_async,
        args=(instance.product, instance)
    )
    thread.daemon = True
    thread.start()
