from django import forms
from django.contrib import admin
from django.db import models

from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase, SortableAdminMixin
from image_uploader_widget.widgets import ImageUploaderWidget

from .models import Category, SubCategory, ProductImage, ProductVariant, Product


class ImageWidgetMixin:
    formfield_overrides = {
        models.ImageField: {'widget': ImageUploaderWidget},
    }


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, ImageWidgetMixin, admin.ModelAdmin):
    list_display = ('order', 'name', 'gender')
    list_editable = ()
    list_filter = ('gender',)
    search_fields = ('name',)
    sortable = 'order'
    change_list_template = 'admin/catalog/category/change_list.html'


@admin.register(SubCategory)
class SubCategoryAdmin(SortableAdminMixin, ImageWidgetMixin, admin.ModelAdmin):
    list_display = ('show_on_main', 'name', 'category', 'is_material', 'size_model')
    list_filter = ('show_on_main', 'category__gender', 'category', 'is_material', 'size_model')
    list_display_links = ('name',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')

    sortable = 'order'
    exclude = ('order',)

    fieldsets = (
        (None, {
            'fields': (
                'category',
                'name',
                'description',
            )
        }),
        ('Отображение и логика', {
            'fields': (
                'show_on_main',
                'is_material',
                'size_model',
                'cover_image',
            )
        }),
    )


class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
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
        from .models import SubCategory
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
        'is_visible',
    )

    search_fields = ('name', 'description', 'material')

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
