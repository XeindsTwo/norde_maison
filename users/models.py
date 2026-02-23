import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class EmailActivation(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(hours=24)

    def __str__(self):
        return f"Activation: {self.user.username}"


@receiver(post_save, sender=User)
def create_user_related(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        EmailActivation.objects.create(user=instance)
