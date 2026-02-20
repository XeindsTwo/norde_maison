from django import forms
from django.contrib import admin
from django.db import models
from django.utils.html import mark_safe
from django.urls import reverse
from django.utils.safestring import mark_safe
from adminsortable2.admin import SortableAdminMixin

from image_uploader_widget.widgets import ImageUploaderWidget

from .models import Category, SubCategory, Product, ProductImage, ProductVariant


class SubCategoryAdminForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = "__all__"

    class Media:
        css = {
            'all': ('admin/custom_admin.css',)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        categories = Category.objects.all().order_by('gender', 'order', 'name')

        grouped_choices = []

        for gender, label in [('F', 'Женские'), ('M', 'Мужские')]:
            items = [
                (cat.id, cat.name)
                for cat in categories.filter(gender=gender)
            ]
            if items:
                grouped_choices.append((label, items))

        self.fields['category'].choices = grouped_choices


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'gender', 'order')
    list_editable = ('order',)
    list_filter = ('gender',)
    search_fields = ('name',)
    ordering = ('order',)


@admin.register(SubCategory)
class SubCategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = SubCategoryAdminForm

    list_display = (
        'image_preview',
        'name',
        'category',
        'is_material',
        'show_on_main',
        'order',
    )
    list_filter = (
        'category__gender',
        'category',
        'is_material',
        'show_on_main'
    )
    search_fields = ('name', 'category__name')
    ordering = ('order',)
    list_display_links = ('name',)
    fields = (
        'image_preview_large',
        'cover_image',
        'name',
        'category',
        'description',
        'is_material',
        'show_on_main',
        'order',
    )

    readonly_fields = ('image_preview_large',)

    formfield_overrides = {
        models.ImageField: {
            'widget': ImageUploaderWidget(attrs={'show_preview': True})
        },
    }

    def image_preview(self, obj):
        if obj.cover_image:
            return mark_safe(
                f'<img src="{obj.cover_image.url}" '
                f'style="height:100px; width:80px; border-radius:8px; object-fit:cover;" />'
            )
        return "—"

    image_preview.short_description = "Превью"

    def image_preview_large(self, obj):
        if obj and obj.cover_image:
            return mark_safe(
                f'<div style="margin-bottom:15px;">'
                f'<img src="{obj.cover_image.url}" '
                f'style="max-height:220px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.15);" />'
                f'</div>'
            )
        return "Сохраните объект, чтобы увидеть превью"

    image_preview_large.short_description = "Текущее изображение"


class ImageWidgetMixin:
    formfield_overrides = {
        models.ImageField: {'widget': ImageUploaderWidget},
    }


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    fields = ['image']
    readonly_fields = []
    extra = 1

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "image":
            kwargs['widget'] = ImageUploaderWidget(attrs={'show_preview': True})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['color_name', 'color_hex', 'size', 'stock', 'delete_row', 'duplicate_row']
    readonly_fields = ['delete_row', 'duplicate_row']

    class Media:
        js = ('admin/product_variant_duplicate.js',)  # подключаем JS для дублирования

    def delete_row(self, obj=None):
        return mark_safe('<span>Удалить</span>')

    delete_row.short_description = 'Удалить?'

    def duplicate_row(self, obj=None):
        return mark_safe('<button type="button" class="duplicate-row-btn">Duplicate</button>')

    duplicate_row.short_description = 'Дублировать?'


class ProductAdminForm(forms.ModelForm):
    material = forms.ChoiceField(label="Материал", required=True)

    class Meta:
        model = Product
        fields = "__all__"

    class Media:
        css = {
            'all': ('admin/custom_admin.css',)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Подкатегории (без материалов)
        qs = SubCategory.objects.filter(is_material=False).select_related('category').order_by(
            'category__gender', 'category__order', 'order', 'name'
        )
        choices = []
        for gender, label in [('F', 'Женские'), ('M', 'Мужские')]:
            items = [(sc.id, f"{sc.name} — {sc.category.name}") for sc in qs.filter(category__gender=gender)]
            if items:
                choices.append((label, items))
        self.fields['subcategory'].choices = choices

        # Материалы
        mat_qs = SubCategory.objects.filter(is_material=True).select_related('category').order_by(
            'category__gender', 'order', 'name'
        )
        mat_choices = []
        for gender, label in [('F', 'Женские материалы'), ('M', 'Мужские материалы')]:
            items = [(m.name, m.name) for m in mat_qs.filter(category__gender=gender)]
            if items:
                mat_choices.append((label, items))
        self.fields['material'].choices = mat_choices


try:
    admin.site.unregister(Product)
except admin.sites.NotRegistered:
    pass


@admin.register(Product)
class ProductAdmin(ImageWidgetMixin, admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'is_visible', 'name', 'subcategory', 'material', 'price_rub', 'created_short', 'colors_preview', 'main_preview'
    )
    list_display_links = ('name',)
    list_filter = ('subcategory__category__gender', 'subcategory__category', 'subcategory', 'is_visible')
    search_fields = ('name', 'description', 'material')
    inlines = [ProductVariantInline, ProductImageInline]
    fields = ('is_visible', 'subcategory', 'material', 'name', 'description', 'price', 'main_image')

    def main_preview(self, obj):
        if obj.main_image:
            return mark_safe(f'<img src="{obj.main_image.url}" style="height:100px; width:80px; border-radius:8px; object-fit:cover;">')
        return "-"

    main_preview.short_description = "Главное фото"

    def price_rub(self, obj):
        return f"{obj.price} ₽"

    price_rub.short_description = "Цена"
    price_rub.admin_order_field = "price"

    def created_short(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')

    created_short.short_description = "Создан"
    created_short.admin_order_field = "created_at"

    def colors_preview(self, obj):
        return obj.colors_preview()

    colors_preview.short_description = "Цвета"
