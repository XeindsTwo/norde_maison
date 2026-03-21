import uuid
from django.db import models
from django.db.models import JSONField
from django.conf import settings
from django.utils import timezone

class OrderStatus(models.TextChoices):
    PENDING = "pending", "Ожидает оплаты"
    ASSEMBLY = "assembly", "В сборке"
    IN_WAY = "in_way", "В пути"
    DELIVERED = "delivered", "Доставлен"
    CANCELLED = "cancelled", "Отменен"

class DeliveryMethod(models.TextChoices):
    CDEK_PVZ = "cdek_pvz", "СДЭК — пункт выдачи"
    CDEK_COURIER = "cdek_courier", "СДЭК — курьер"

class Country(models.TextChoices):
    RU = "RU", "Российская Федерация"
    KZ = "KZ", "Казахстан"
    BY = "BY", "Беларусь"

def generate_order_number():
    return uuid.uuid4().hex[:10].upper()

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь"
    )
    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name="Номер заказа"
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.ASSEMBLY,
        verbose_name="Статус"
    )
    payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID платежа YooKassa"
    )
    country = models.CharField(
        max_length=2,
        choices=Country.choices,
        verbose_name="Страна"
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DeliveryMethod.choices,
        verbose_name="Способ доставки"
    )
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Имя")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Телефон")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram")
    address = models.TextField(blank=True, verbose_name="Адрес")
    delivery_extra = JSONField(blank=True, null=True, verbose_name="Доп. данные доставки")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    notified = models.BooleanField(default=False)
    delivery_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Стоимость доставки"
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Итоговая сумма"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.order_number:
            self.order_number = f"{self.id:06d}"
            super().save(update_fields=["order_number"])

    def __str__(self):
        return f"№{self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="Заказ"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Вариант товара"
    )
    product_name = models.CharField(max_length=300, verbose_name="Название товара")
    color = models.CharField(max_length=100, verbose_name="Цвет")
    size = models.CharField(max_length=20, verbose_name="Размер")
    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Цена на момент покупки"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def subtotal(self):
        return self.price_snapshot * self.quantity