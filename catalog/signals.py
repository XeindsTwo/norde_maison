import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Product, ProductImage, SubCategory

def safe_delete_file(file_field):
    """Удаляет файл с диска, если он существует."""
    if file_field and file_field.path and os.path.exists(file_field.path):
        try:
            os.remove(file_field.path)
        except Exception:
            pass  # на проде можно логировать исключение

# --- Продукты ---
@receiver(post_delete, sender=Product)
def delete_product_files(sender, instance, **kwargs):
    safe_delete_file(instance.main_image)
    for img in instance.images.all():
        safe_delete_file(img.image)

# --- Изображения продукта ---
@receiver(post_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    safe_delete_file(instance.image)

# --- Подкатегории ---
@receiver(post_delete, sender=SubCategory)
def delete_subcategory_related(sender, instance, **kwargs):
    instance.products.all().delete()
    safe_delete_file(instance.cover_image)