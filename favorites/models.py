from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name="favorites",
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        related_name="favorited_by",
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(
        verbose_name="Дата добавления",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Популярные избранные товары"
        unique_together = ("user", "product")
        indexes = [
            models.Index(fields=["user", "product"]),
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.product.name}"
