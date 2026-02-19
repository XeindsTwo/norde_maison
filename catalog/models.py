import uuid
import os

from django.db import models
from django.core.validators import MinValueValidator
from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from django.utils.html import format_html, mark_safe


def product_main_image_path(instance, filename):
    ext = filename.split('.')[-1]
    new_name = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('products/main/', new_name)


def product_gallery_image_path(instance, filename):
    ext = filename.split('.')[-1]
    new_name = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('products/gallery/', new_name)


def subcategory_cover_path(instance, filename):
    ext = filename.split('.')[-1]
    new_name = f'{uuid.uuid4().hex}.{ext}'
    return os.path.join('subcategories/', new_name)


def validate_image_size(image):
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Размер файла не должен превышать {max_size_mb} МБ')


class Category(models.Model):
    class Gender(models.TextChoices):
        MEN = 'M', 'Мужской'
        WOMEN = 'F', 'Женский'

    name = models.CharField('Название категории', max_length=200)
    gender = models.CharField('Пол', max_length=1, choices=Gender.choices)
    order = models.PositiveIntegerField('Порядок вывода', default=1, help_text='Порядок вывода в меню')

    class Meta:
        ordering = ['order', 'gender', 'name']
        verbose_name = 'категорию'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return f'{self.name} ({self.get_gender_display()})'


class SubCategory(models.Model):
    class SizeModel(models.TextChoices):
        STANDARD = 'standard', 'XXS–XXL'
        UNI = 'uni', 'UNI'

    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    name = models.CharField('Название подкатегории', max_length=200)
    size_model = models.CharField(
        'Модель размеров',
        max_length=20,
        choices=SizeModel.choices,
        help_text='Модель размеров для товаров в этой подкатегории',
    )
    cover_image = models.ImageField(
        'Обложка подкатегории',
        upload_to=subcategory_cover_path,
        null=True,
        blank=False,
        validators=[validate_image_size],
    )
    show_on_main = models.BooleanField(
        'Показывать на главной',
        default=False,
        help_text='Показывать на главной (для выбора 4-х подкатегорий)',
    )
    is_material = models.BooleanField(
        'Является материалом',
        default=False,
        help_text='Отметь, если эта подкатегория — раздел материалов',
    )
    description = models.TextField(
        'Описание подкатегории',
        blank=True,
        default='',
        help_text='Краткое описание (Футболки, блузки, комплекты и т.п.)',
    )
    order = models.PositiveIntegerField('Порядок вывода', default=1, help_text='Порядок вывода')

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'подкатегорию'
        verbose_name_plural = 'Подкатегории'

    def delete(self, *args, **kwargs):
        if self.cover_image:
            self.cover_image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        gender = self.category.get_gender_display()
        return f'[{gender}] {self.name} — {self.category.name}'


class Product(models.Model):
    subcategory = models.ForeignKey(
        SubCategory,
        verbose_name='Подкатегория',
        on_delete=models.CASCADE,
        related_name='products',
    )
    material = models.CharField(
        'Материал',
        max_length=200,
        blank=True,
        default='',
        help_text='Например: Хлопок, Лен, Шерсть мериноса',
    )
    name = models.CharField('Название товара', max_length=300)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField(
        'Цена',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_visible = models.BooleanField('Доступность', default=True)
    main_image = models.ImageField(
        'Главное изображение',
        upload_to=product_main_image_path,
        null=True,
        blank=False,
        validators=[validate_image_size],
        help_text='Главное изображение товара',
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def delete(self, *args, **kwargs):
        if self.main_image:
            self.main_image.delete(save=False)
        for img in self.images.all():
            if img.image:
                img.image.delete(save=False)
        super().delete(*args, **kwargs)

    def colors_preview(self):
        variants = self.variants.all()
        if not variants:
            return '—'
        unique_colors = {v.color_hex: v.color_name for v in variants}
        items = []
        for hex_code, name in unique_colors.items():
            items.append(
                f'<span title="{name}" '
                f'style="display:inline-block; width: 14px; height: 14px; '
                f'border-radius: 10%; margin-right: 4px; '
                f'border: 1px solid #ccc; background-color: {hex_code};"></span>'
            )
        return mark_safe(''.join(items))

    colors_preview.short_description = 'Цвета'

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(
        'Изображение',
        upload_to=product_gallery_image_path,
        validators=[validate_image_size],
    )
    order = models.PositiveIntegerField('Порядок вывода', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Фотография товара'
        verbose_name_plural = 'Фотографии товара'

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def preview_image(self):
        if self.image:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: cover;" />',
                self.image.url,
            )
        return 'Нет изображения'

    preview_image.short_description = 'Превью'

    def __str__(self):
        return f'{self.product.name} — {self.order}'


class ProductVariant(models.Model):
    class Sizes(models.TextChoices):
        XXS = 'XXS', 'XXS'
        XS = 'XS', 'XS'
        S = 'S', 'S'
        M = 'M', 'M'
        L = 'L', 'L'
        XL = 'XL', 'XL'
        XXL = 'XXL', 'XXL'
        UNI = 'UNI', 'UNI'

    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='variants',
    )
    color_name = models.CharField(
        'Название цвета',
        max_length=50,
        help_text='Например: Коричневый, Серый, Лавандовый',
    )
    color_hex = ColorField(
        'Цвет',
        default='#000000',
        help_text='HEX-значение для кружочка, например #5C3A21',
    )
    size = models.CharField('Размер', max_length=10, choices=Sizes.choices)
    stock = models.PositiveIntegerField(
        'Остаток на складе',
        default=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        unique_together = ('product', 'color_name', 'size')
        verbose_name = 'Вариант товара'
        verbose_name_plural = 'Варианты товара'

    def clean(self):
        super().clean()
        size_model = self.product.subcategory.size_model
        if size_model == SubCategory.SizeModel.UNI and self.size != ProductVariant.Sizes.UNI:
            raise ValidationError({'size': 'Для этой подкатегории допускается только размер UNI.'})
        if size_model == SubCategory.SizeModel.STANDARD and self.size == ProductVariant.Sizes.UNI:
            raise ValidationError({'size': 'Для стандартной модели размеров UNI использовать нельзя.'})

    def __str__(self):
        return f'{self.product.name} / {self.color_name} / {self.size}'