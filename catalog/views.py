from rest_framework import generics, permissions

from .models import Category, SubCategory, Product
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)


class CategoryListView(generics.ListAPIView):
    """
    Список категорий с фильтрацией по полу и по материалам.
    - gender=M/F
    - is_material=true/false
    Если для выбранного фильтра нет подкатегорий, категория не возвращается.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Category.objects.all()
        gender = self.request.query_params.get('gender')
        is_material = self.request.query_params.get('is_material')

        if gender in ('M', 'F'):
            qs = qs.filter(gender=gender)

        if is_material is not None:
            val = is_material.lower() in ('1', 'true', 'yes')
            # оставляем только категории, у которых есть подкатегории с нужным is_material
            qs = qs.filter(subcategories__is_material=val)
            qs = qs.distinct()

        return qs.order_by('order', 'name')


class SubCategoryListView(generics.ListAPIView):
    queryset = SubCategory.objects.select_related('category').all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get('category')
        show_on_main = self.request.query_params.get('show_on_main')
        gender = self.request.query_params.get('gender')

        if category_id:
            qs = qs.filter(category_id=category_id)
        if show_on_main is not None:
            if show_on_main.lower() in ('1', 'true', 'yes'):
                qs = qs.filter(show_on_main=True)
        if gender:
            qs = qs.filter(category__gender=gender)

        # фильтруем материалы только если category не Материалы
        if category_id:
            cat = Category.objects.filter(id=category_id).first()
            if cat and cat.name != 'Материалы':
                qs = qs.filter(is_material=False)

        return qs


class ProductListView(generics.ListAPIView):
    """
    Список товаров (каталог). Фильтры:
    - subcategory
    - category (через subcategory__category)
    - gender (через subcategory__category__gender)
    - is_visible
    """
    queryset = Product.objects.select_related(
        'subcategory',
        'subcategory__category',
        'material',
    ).prefetch_related('images', 'variants')
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        subcategory_id = self.request.query_params.get('subcategory')
        category_id = self.request.query_params.get('category')
        gender = self.request.query_params.get('gender')
        visible = self.request.query_params.get('visible')

        if subcategory_id:
            qs = qs.filter(subcategory_id=subcategory_id)
        if category_id:
            qs = qs.filter(subcategory__category_id=category_id)
        if gender:
            qs = qs.filter(subcategory__category__gender=gender)
        if visible is not None:
            if visible.lower() in ('1', 'true', 'yes'):
                qs = qs.filter(is_visible=True)
        return qs


class ProductDetailView(generics.RetrieveAPIView):
    """
    Детальная карточка товара.
    """
    queryset = Product.objects.select_related(
        'subcategory',
        'subcategory__category',
        'material',
    ).prefetch_related('images', 'variants')
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
