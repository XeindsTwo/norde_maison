from django.contrib import admin
from django.utils.html import mark_safe
from django.urls import reverse
from .models import Order, OrderItem, OrderStatus


def fmt_price(value):
    try:
        amount = float(value)
        whole = int(amount)
        frac = round((amount - whole) * 100)
        formatted = f"{whole:,}".replace(",", " ")
        return f"{formatted},{frac:02d} ₽"
    except (TypeError, ValueError):
        return "—"


STATUS_CONFIG = {
    "assembly":   ("#fef3c7", "#d97706", "В сборке"),
    "in_way":     ("#dbeafe", "#1d4ed8", "В пути"),
    "delivered":  ("#d1ecf1", "#0c5460", "Доставлен"),
    "cancelled":  ("#f8d7da", "#721c24", "Отменён"),
}

COUNTRY_SHORT = {
    "RU": "РФ",
    "KZ": "КЗ",
    "BY": "РБ",
}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    verbose_name = "Позиция заказа"
    verbose_name_plural = "Позиции заказа"
    fields = (
        "product_preview",
        "product_link",
        "color_display",
        "size",
        "quantity",
        "price_snapshot_display",
        "subtotal_display",
    )
    readonly_fields = fields

    class Media:
        css = {"all": ("admin/custom_admin.css",)}

    def has_add_permission(self, request, obj=None):
        return False

    def product_preview(self, obj):
        if obj.variant and obj.variant.product and obj.variant.product.main_image:
            return mark_safe(
                f'<img src="{obj.variant.product.main_image.url}" '
                f'style="height:60px; width:48px; border-radius:6px; object-fit:cover;" />'
            )
        return "—"
    product_preview.short_description = "Фото"

    def product_link(self, obj):
        if obj.variant and obj.variant.product:
            url = reverse("admin:catalog_product_change", args=[obj.variant.product.pk])
            return mark_safe(f'<a href="{url}">{obj.product_name}</a>')
        return obj.product_name
    product_link.short_description = "Название товара"

    def color_display(self, obj):
        if obj.variant and obj.variant.color_hex:
            return mark_safe(
                f'<div style="display:flex; align-items:center; gap:8px;">'
                f'<span style="display:inline-block; width:16px; height:16px; border-radius:3px; '
                f'background:{obj.variant.color_hex}; border:1px solid rgba(0,0,0,0.15);"></span>'
                f'{obj.color}</div>'
            )
        return obj.color
    color_display.short_description = "Цвет"

    def price_snapshot_display(self, obj):
        return fmt_price(obj.price_snapshot)
    price_snapshot_display.short_description = "Цена на момент покупки"

    def subtotal_display(self, obj):
        if obj.price_snapshot and obj.quantity:
            return fmt_price(obj.price_snapshot * obj.quantity)
        return "—"
    subtotal_display.short_description = "Сумма"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status_badge",
        "country_short",
        "total_price_display",
        "delivery_price_display",
        "created_at",
    )
    list_filter = (
        "status",
        "country",
        "delivery_method",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "order_number",
        "user__email",
        "user__username",
    )
    ordering = ("-created_at",)
    inlines = [OrderItemInline]
    readonly_fields = (
        "order_number",
        "user_display",
        "country",
        "delivery_method",
        "created_at",
        "total_price_detail",
        "delivery_price_detail",
        "delivery_extra_display",
        "comment_display",
        "fio_display",
        "telegram_display",
        "phone_display",
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj and obj.status == OrderStatus.CANCELLED:
            if 'status' not in readonly_fields:
                readonly_fields.append('status')
        return readonly_fields

    fieldsets = (
        ("Заказ", {
            "fields": (
                "status",
                "order_number",
                "user_display",
                "fio_display",
                "phone_display",
                "telegram_display",
                "total_price_detail",
                "created_at",
            )
        }),
        ("Доставка", {
            "fields": (
                "country",
                "delivery_method",
                "address",
                "delivery_extra_display",
                "comment_display",
                "delivery_price_detail",
            )
        }),
    )

    def status_badge(self, obj):
        bg, color, label = STATUS_CONFIG.get(obj.status, ("#f0f0f0", "#555555", obj.status))
        return mark_safe(
            f'<span style="padding:4px 12px; border-radius:16px; font-size:13px; '
            f'font-weight:600; background:{bg}; color:{color}; box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
            f'{label}</span>'
        )
    status_badge.short_description = "Статус"

    def country_short(self, obj):
        return COUNTRY_SHORT.get(obj.country, obj.country)
    country_short.short_description = "Страна"

    def user_display(self, obj):
        return str(obj.user)
    user_display.short_description = "Пользователь"

    def fio_display(self, obj):
        parts = [obj.last_name, obj.first_name]
        if obj.middle_name:
            parts.append(obj.middle_name)
        result = " ".join(p for p in parts if p)
        return result if result.strip() else "Не указано"
    fio_display.short_description = "ФИО"

    def phone_display(self, obj):
        return obj.phone if obj.phone else "Не указано"
    phone_display.short_description = "Телефон"

    def telegram_display(self, obj):
        return obj.telegram if obj.telegram else "Не указано"
    telegram_display.short_description = "Telegram"

    def total_price_display(self, obj):
        return fmt_price(obj.total_price)
    total_price_display.short_description = "Итоговая сумма"
    total_price_display.admin_order_field = "total_price"

    def total_price_detail(self, obj):
        return fmt_price(obj.total_price)
    total_price_detail.short_description = "Итоговая сумма"

    def delivery_price_display(self, obj):
        if obj.delivery_price == 0:
            return mark_safe('<span style="color:#10b981; font-weight:600;">Бесплатно</span>')
        return fmt_price(obj.delivery_price)
    delivery_price_display.short_description = "Доставка"
    delivery_price_display.admin_order_field = "delivery_price"

    def delivery_price_detail(self, obj):
        if obj.delivery_price == 0:
            return "Бесплатно"
        return fmt_price(obj.delivery_price)
    delivery_price_detail.short_description = "Стоимость доставки"

    def delivery_extra_display(self, obj):
        if not obj.delivery_extra:
            return "—"
        extra = obj.delivery_extra
        parts = []
        if extra.get("entrance"):
            parts.append(f"Подъезд (дом): {extra['entrance']}")
        if extra.get("floor"):
            parts.append(f"Этаж: {extra['floor']}")
        if extra.get("apartment"):
            parts.append(f"Квартира: {extra['apartment']}")
        return mark_safe(" &nbsp;·&nbsp; ".join(parts)) if parts else "—"
    delivery_extra_display.short_description = "Подъезд (дом) / Этаж / Квартира"

    def comment_display(self, obj):
        return obj.comment if obj.comment else "Не указано"
    comment_display.short_description = "Комментарий"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return None

    class Media:
        css = {"all": ("admin/custom_admin.css",)}