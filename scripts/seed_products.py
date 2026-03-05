import os
import sys
import random
from pathlib import Path

import django
from faker import Faker
from django.core.files import File

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "norde_maison.settings")

django.setup()

from catalog.models import Product, ProductImage, ProductVariant, SubCategory

fake = Faker("ru_RU")

SEED_MEDIA_PATH = PROJECT_ROOT / "media_seed" / "products"

COLORS = [
    ("Черный", "#292b34"),
    ("Коричневый", "#5c4939"),
    ("Серый", "#898e8c"),
    ("Белый", "#ffffff"),
    ("Бежевый", "#d6c3a3"),
    ("Синий", "#2f4b7c"),
    ("Зеленый", "#3a6b35"),
    ("Красный", "#c0392b"),
    ("Розовый", "#e84393"),
    ("Фиолетовый", "#6c5ce7"),
    ("Жёлтый", "#f1c40f"),
    ("Оранжевый", "#e67e22"),
    ("Голубой", "#3498db"),
    ("Бирюзовый", "#1abc9c"),
]

SIZES = ["XS", "S", "M", "L", "XL"]

SKIRT_NAMES = [
    "Юбка миди",
    "Юбка-карандаш",
    "Юбка плиссе",
    "Юбка А-силуэта",
    "Юбка с высокой талией",
    "Юбка из хлопка",
    "Юбка из вискозы",
    "Юбка классическая",
    "Юбка минималистичная",
    "Юбка струящаяся",
    "Юбка летняя",
    "Юбка повседневная",
    "Юбка офисная",
    "Юбка премиум",
    "Юбка базовая",
    "Юбка вечерняя",
    "Юбка длинная",
    "Юбка короткая",
    "Юбка трикотажная",
    "Юбка дизайнерская"
]


def generate_product_name():
    base = random.choice(SKIRT_NAMES)

    if random.random() < 0.5:
        suffix = random.choice([
            "Norde",
            "Maison",
            "Edition",
            "Soft Line",
            "Essential",
            "Luxury",
            "Urban",
            "Classic"
        ])
        base += f" {suffix}"

    if random.random() < 0.3:
        base += f" {random.randint(2023, 2025)}"

    return base


def get_price():
    return random.randint(2300, 23000) + random.choice([0, 49, 90, 99])


def get_variant_color_count():
    r = random.random()

    if r < 0.3:
        return 1
    elif r < 0.7:
        return 2
    elif r < 0.9:
        return 3
    return 4


def get_skirt_subcategories():
    return SubCategory.objects.filter(
        category__gender="F",
        name__icontains="юбк"
    )


def collect_seed_images():
    images = []

    skirt_path = SEED_MEDIA_PATH / "skirt"

    if not skirt_path.exists():
        return images

    for root, _, files in os.walk(skirt_path):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                images.append(Path(root) / file)

    return images


def seed_skirt_products(count=70):
    subcategories = list(get_skirt_subcategories())

    if not subcategories:
        print("Нет подкатегорий юбок")
        return

    images_pool = collect_seed_images()

    if not images_pool:
        print("Нет seed изображений")
        return

    print(f"Генерация {count} товаров юбок...")

    for _ in range(count):

        product = Product.objects.create(
            subcategory=random.choice(subcategories),
            name=generate_product_name(),
            description=fake.paragraph(nb_sentences=5),
            price_rub=get_price(),
            price_kzt=get_price() * 5,
            price_byn=get_price() / 3,
            material=random.choice(["Хлопок", "Вискоза", "Полиэстер", "Лён"]),
            is_visible=True,
        )

        img_path = random.choice(images_pool)

        with open(img_path, "rb") as f:
            product.main_image.save(img_path.name, File(f), save=True)

        for _ in range(random.randint(1, 3)):
            img_path = random.choice(images_pool)

            with open(img_path, "rb") as f:
                ProductImage.objects.create(
                    product=product,
                    image=File(f),
                    order=random.randint(0, 5),
                )

        used_pairs = set()

        color_count = random.randint(1, 4)

        selected_colors = random.sample(
            COLORS,
            min(color_count, len(COLORS))
        )

        sizes = random.sample(
            SIZES,
            random.randint(2, len(SIZES))
        )

        for color_name, color_hex in selected_colors:
            for size in sizes:

                if len(used_pairs) >= random.randint(4, 10):
                    break

                if (color_hex, size) in used_pairs:
                    continue

                used_pairs.add((color_hex, size))

                ProductVariant.objects.create(
                    product=product,
                    color_name=color_name,
                    color_hex=color_hex,
                    size=size,
                    stock=random.randint(0, 200),
                )

    print("Seed юбок завершён")


if __name__ == "__main__":
    seed_skirt_products(70)