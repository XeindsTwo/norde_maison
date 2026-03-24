from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import mark_safe
from .models import DeliveryRegion, TelegramConfig, SiteConfig


class SingletonAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        return HttpResponseRedirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=[obj.pk],
            )
        )


@admin.register(DeliveryRegion)
class DeliveryRegionAdmin(admin.ModelAdmin):
    list_display = ("country_display", "pvz_display", "courier_display")

    def _symbol(self, obj):
        return {"KZ": "₸", "BY": "Br"}.get(obj.code, "₽")

    def _prices(self, obj):
        if obj.code == "KZ":
            return {
                "pvz": obj.cdek_pvz_price_kzt,
                "pvz_free": obj.cdek_pvz_free_from_kzt,
                "courier": obj.cdek_courier_price_kzt,
                "courier_free": obj.cdek_courier_free_from_kzt,
            }
        if obj.code == "BY":
            return {
                "pvz": obj.cdek_pvz_price_byn,
                "pvz_free": obj.cdek_pvz_free_from_byn,
                "courier": obj.cdek_courier_price_byn,
                "courier_free": obj.cdek_courier_free_from_byn,
            }
        return {
            "pvz": obj.cdek_pvz_price,
            "pvz_free": obj.cdek_pvz_free_from,
            "courier": obj.cdek_courier_price,
            "courier_free": obj.cdek_courier_free_from,
        }

    def country_display(self, obj):
        return obj.get_code_display()
    country_display.short_description = "Страна"

    def pvz_display(self, obj):
        s = self._symbol(obj)
        p = self._prices(obj)
        return mark_safe(f"{p['pvz']} {s} &nbsp;·&nbsp; бесплатно от {p['pvz_free']} {s}")
    pvz_display.short_description = "ПВЗ CDEK"

    def courier_display(self, obj):
        s = self._symbol(obj)
        p = self._prices(obj)
        return mark_safe(f"{p['courier']} {s} &nbsp;·&nbsp; бесплатно от {p['courier_free']} {s}")
    courier_display.short_description = "Курьер CDEK"

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                ("Регион", {"fields": ("code",)}),
            )

        if obj.code == "RU":
            symbol = "₽"
            pvz_price, pvz_free = "cdek_pvz_price", "cdek_pvz_free_from"
            courier_price, courier_free = "cdek_courier_price", "cdek_courier_free_from"

        elif obj.code == "KZ":
            symbol = "₸"
            pvz_price, pvz_free = "cdek_pvz_price_kzt", "cdek_pvz_free_from_kzt"
            courier_price, courier_free = "cdek_courier_price_kzt", "cdek_courier_free_from_kzt"

        elif obj.code == "BY":
            symbol = "Br"
            pvz_price, pvz_free = "cdek_pvz_price_byn", "cdek_pvz_free_from_byn"
            courier_price, courier_free = "cdek_courier_price_byn", "cdek_courier_free_from_byn"

        else:
            return (
                ("Регион", {"fields": ("code",)}),
            )

        return (
            ("Регион", {"fields": ("code",)}),
            (f"В пункт выдачи CDEK — {symbol}", {"fields": (pvz_price, pvz_free)}),
            (f"Курьером CDEK по адресу — {symbol}", {"fields": (courier_price, courier_free)}),
        )


@admin.register(TelegramConfig)
class TelegramConfigAdmin(SingletonAdmin):
    fieldsets = (
        ("Telegram бот", {"fields": ("bot_token", "group_id")}),
    )


@admin.register(SiteConfig)
class SiteConfigAdmin(SingletonAdmin):
    fieldsets = (
        ("Ссылки сайта", {"fields": ("channel_url", "support_url")}),
    )