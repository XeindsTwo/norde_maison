from rest_framework import generics, permissions

from .models import Category, SubCategory, Product
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        gender = self.request.query_params.get('gender')
        is_material = self.request.query_params.get('is_material')

        if gender:
            qs = qs.filter(gender=gender)
        if is_material is not None:
            if is_material.lower() in ('1', 'true', 'yes'):
                qs = qs.filter(is_material=True)
            if is_material.lower() in ('0', 'false', 'no'):
                qs = qs.filter(is_material=False)
        return qs


class SubCategoryListView(generics.ListAPIView):
    queryset = SubCategory.objects.select_related('category').all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get('category')
        show_on_main = self.request.query_params.get('show_on_main')

        if category_id:
            qs = qs.filter(category_id=category_id)
        if show_on_main is not None:
            if show_on_main.lower() in ('1', 'true', 'yes'):
                qs = qs.filter(show_on_main=True)
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
