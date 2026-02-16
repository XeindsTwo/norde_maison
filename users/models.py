from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    phone = models.CharField(
        'Телефон',
        max_length=50,
        blank=True,
    )
    tg_username = models.CharField(
        'Telegram',
        max_length=100,
        blank=True,
        help_text='Ник в Telegram, например @username',
    )
    address = models.TextField(
        'Адрес',
        blank=True,
        help_text='Основной адрес доставки',
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль: {self.user.username}'