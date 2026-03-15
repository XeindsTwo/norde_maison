from django.db import models


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class DeliveryRegion(models.Model):
    REGIONS = [
        ("RU", "Российская Федерация"),
        ("BY", "Республика Беларусь"),
        ("KZ", "Республика Казахстан"),
    ]

    code = models.CharField(max_length=2, choices=REGIONS, unique=True, verbose_name="Страна")

    # RUB
    cdek_pvz_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ПВЗ — цена (₽)")
    cdek_pvz_free_from = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ПВЗ — бесплатно от (₽)")
    cdek_courier_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Курьер — цена (₽)")
    cdek_courier_free_from = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Курьер — бесплатно от (₽)")

    # KZT
    cdek_pvz_price_kzt = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ПВЗ — цена (₸)")
    cdek_pvz_free_from_kzt = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ПВЗ — бесплатно от (₸)")
    cdek_courier_price_kzt = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Курьер — цена (₸)")
    cdek_courier_free_from_kzt = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Курьер — бесплатно от (₸)")

    # BYN
    cdek_pvz_price_byn = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ПВЗ — цена (Br)")
    cdek_pvz_free_from_byn = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="ПВЗ — бесплатно от (Br)")
    cdek_courier_price_byn = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Курьер — цена (Br)")
    cdek_courier_free_from_byn = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Курьер — бесплатно от (Br)")

    class Meta:
        verbose_name = "Настройки доставки"
        verbose_name_plural = "Доставка"

    def __str__(self):
        return dict(self.REGIONS)[self.code]


class TelegramConfig(SingletonModel):
    bot_token = models.CharField(max_length=255, blank=True, verbose_name="Токен Telegram бота")
    group_id = models.CharField(max_length=255, blank=True, verbose_name="ID группы для уведомлений")

    class Meta:
        verbose_name = "Telegram настройки"
        verbose_name_plural = "Telegram настройки"

    def __str__(self):
        return "Telegram конфигурация"


class SiteConfig(SingletonModel):
    channel_url = models.URLField(blank=True, verbose_name="Telegram канал")
    support_url = models.URLField(blank=True, verbose_name="Telegram поддержка")

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"