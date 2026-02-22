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
    "Юбка повседневная"
]


def generate_product_name():
    base = random.choice(SKIRT_NAMES)

    suffixes = [
        "",
        "Norde",
        "Maison",
        "Edition",
        "Soft Line",
        "Essential"
    ]

    if random.random() < 0.5:
        base += f" {random.choice(suffixes)}"

    return base


def get_variant_color_count():
    r = random.random()

    if r < 0.3:
        return 1
    elif r < 0.7:
        return 2
    elif r < 0.9:
        return 3
    else:
        return 4


def get_skirt_subcategories():
    return SubCategory.objects.filter(
        category__gender="F",
        name__icontains="юбк"
    )


def collect_skirt_seed_images():
    images = []

    skirt_path = SEED_MEDIA_PATH / "skirt"

    if not skirt_path.exists():
        return images

    for root, _, files in os.walk(skirt_path):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                images.append(Path(root) / file)

    return images


def seed_skirt_products(count=40):
    subcategories = list(get_skirt_subcategories())

    if not subcategories:
        print("Нет подкатегории юбок")
        return

    images_pool = collect_skirt_seed_images()

    if not images_pool:
        print("Нет изображений в skirt seed папке")
        return

    print(f"Генерация {count} товаров для юбок...")

    for _ in range(count):
        subcategory = random.choice(subcategories)

        product = Product.objects.create(
            subcategory=subcategory,
            name=generate_product_name(),
            description=fake.paragraph(nb_sentences=5),
            price=random.randint(3000, 18000),
            material=random.choice(["Хлопок", "Вискоза", "Полиэстер", "Лён"]),
            is_visible=True,
        )

        # Главное изображение
        try:
            img_path = random.choice(images_pool)

            with open(img_path, "rb") as f:
                product.main_image.save(
                    img_path.name,
                    File(f),
                    save=True,
                )
        except Exception:
            pass

        # Дополнительные изображения
        for _ in range(random.randint(1, 3)):
            try:
                img_path = random.choice(images_pool)

                with open(img_path, "rb") as f:
                    ProductImage.objects.create(
                        product=product,
                        image=File(f),
                        order=random.randint(0, 5),
                    )
            except Exception:
                pass

        # Варианты товара
        used_pairs = set()

        color_variant_count = get_variant_color_count()

        selected_colors = random.sample(
            COLORS,
            min(color_variant_count, len(COLORS))
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

                try:
                    ProductVariant.objects.create(
                        product=product,
                        color_name=color_name,
                        color_hex=color_hex,
                        size=size,
                        stock=random.randint(0, 200),
                    )
                except Exception:
                    pass

    print("Генерация юбок завершена")


if __name__ == "__main__":
    seed_skirt_products(40)
