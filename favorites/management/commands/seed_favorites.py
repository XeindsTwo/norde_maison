import random
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand

from favorites.models import Favorite
from catalog.models import Product
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Заполнить избранное тестовыми данными с датами"

    def handle(self, *args, **kwargs):

        users = list(User.objects.all())
        products = list(Product.objects.filter(is_visible=True))

        if not users or not products:
            self.stdout.write("Нет пользователей или товаров")
            return

        now = timezone.now()

        created_count = 0

        for user in users:
            for _ in range(random.randint(10, 15)):
                product = random.choice(products)
                days_ago = random.randint(1, 30)
                fake_date = now - timedelta(days=days_ago)

                favorite, _ = Favorite.objects.get_or_create(
                    user=user,
                    product=product
                )

                Favorite.objects.filter(
                    id=favorite.id
                ).update(created_at=fake_date)

                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Создано записей избранного: {created_count}"
            )
        )