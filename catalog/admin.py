from django import forms
from django.contrib import admin
from django.db import models

from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase
from image_uploader_widget.widgets import ImageUploaderWidget

from .models import Category, SubCategory, ProductImage, ProductVariant, Product


class ImageWidgetMixin:
    """
    Единый красивый виджет для всех ImageField (cover_image, main_image и т.п.).
    """
    formfield_overrides = {
        models.ImageField: {'widget': ImageUploaderWidget},
    }


@admin.register(Category)
class CategoryAdmin(ImageWidgetMixin, admin.ModelAdmin):
    list_display = ('name', 'gender', 'is_material', 'order')
    list_filter = ('gender', 'is_material')
    search_fields = ('name',)
    ordering = ('order', 'name')


@admin.register(SubCategory)
class SubCategoryAdmin(ImageWidgetMixin, admin.ModelAdmin):
    list_display = ('name', 'category', 'size_model', 'show_on_main', 'order')
    list_filter = ('category__gender', 'category', 'size_model', 'show_on_main')
    search_fields = ('name',)
    ordering = ('order', 'name')

    def get_fields(self, request, obj=None):
        fields = (
            'category',
            'name',
            'size_model',
            'cover_image',
            'show_on_main',
            'order',
        )
        return fields


class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
    """
    Инлайн для фотографий товара:
    - превью (preview_image)
    - drag&drop сортировка по полю order (SortableInlineAdminMixin)
    """
    model = ProductImage
    fields = ['image', 'preview_image']
    readonly_fields = ['preview_image']
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import SubCategory  # избежать циклического импорта

        self.fields['subcategory'].queryset = SubCategory.objects.select_related('category').order_by(
            'category__gender',
            'order',
            'name',
        )


@admin.register(Product)
class ProductAdmin(SortableAdminBase, ImageWidgetMixin, admin.ModelAdmin):
    form = ProductAdminForm

    list_display = (
        'is_visible',
        'name',
        'subcategory',
        'material',
        'price_rub',
        'created_short',
        'colors_preview',
    )
    list_display_links = ('name',)

    list_filter = (
        'subcategory__category__gender',
        'subcategory__category',
        'subcategory',
        'material',
        'is_visible',
    )

    search_fields = ('name', 'description')

    inlines = [ProductVariantInline, ProductImageInline]

    fields = (
        'is_visible',
        'subcategory',
        'material',
        'name',
        'description',
        'price',
        'main_image',
    )

    def price_rub(self, obj):
        return f'{obj.price} ₽'
    price_rub.short_description = 'Цена'
    price_rub.admin_order_field = 'price'

    def created_short(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')
    created_short.short_description = 'Создан'
    created_short.admin_order_field = 'created_at'

    def colors_preview(self, obj):
        return obj.colors_preview()
    colors_preview.short_description = 'Цвета'
