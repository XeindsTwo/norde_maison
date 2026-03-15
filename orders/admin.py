from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "product_name",
        "variant",
        "color",
        "size",
        "quantity",
        "price_snapshot",
        "subtotal_display",
    )
    readonly_fields = fields

    def subtotal_display(self, obj):
        if obj.price_snapshot and obj.quantity:
            return f"{obj.price_snapshot * obj.quantity} ₽"
        return "—"
    subtotal_display.short_description = "Сумма позиции"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "total_price",
        "delivery_price",
        "created_at",
    )
    list_filter = (
        "status",
        "country",
        "delivery_method",
    )
    search_fields = (
        "order_number",
        "user__email",
        "user__username",
    )
    ordering = ("-created_at",)
    list_editable = ("status",)
    inlines = [OrderItemInline]
    readonly_fields = (
        "order_number",
        "created_at",
        "total_price",
        "delivery_price",
    )
    fieldsets = (
        ("Заказ", {
            "fields": (
                "order_number",
                "user",
                "status",
                "country",
                "delivery_method",
            )
        }),
        ("Доставка", {
            "fields": (
                "address",
                "comment",
                "delivery_price",
            )
        }),
        ("Финансы", {
            "fields": ("total_price",)
        }),
        ("Дата создания", {
            "fields": ("created_at",)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return None