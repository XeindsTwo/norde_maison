from rest_framework import generics, permissions
from django.db.models import Q
from .models import Category, SubCategory, Product
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)


class CategoryListView(generics.ListAPIView):
    """Список категорий с фильтрацией по полу и по материалам"""
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
            qs = qs.filter(subcategories__is_material=val).distinct()

        return qs.order_by('order', 'name')


class SubCategoryListView(generics.ListAPIView):
    """Список подкатегорий с фильтрацией"""
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = SubCategory.objects.select_related('category').all()
        category_id = self.request.query_params.get('category')
        show_on_main = self.request.query_params.get('show_on_main')
        gender = self.request.query_params.get('gender')

        if category_id:
            qs = qs.filter(category_id=category_id)
        if show_on_main and show_on_main.lower() in ('1', 'true', 'yes'):
            qs = qs.filter(show_on_main=True)
        if gender:
            qs = qs.filter(category__gender=gender)

        # фильтруем материалы только если категория не Материалы
        if category_id:
            cat = Category.objects.filter(id=category_id).first()
            if cat and cat.name != 'Материалы':
                qs = qs.filter(is_material=False)

        return qs


class ProductListView(generics.ListAPIView):
    """Список товаров с фильтрами"""
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Product.objects.select_related(
            'subcategory', 'subcategory__category'
        ).prefetch_related('images', 'variants')

        subcategory_id = self.request.query_params.get('subcategory')
        category_id = self.request.query_params.get('category')
        gender = self.request.query_params.get('gender')
        visible = self.request.query_params.get('visible')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        size = self.request.query_params.get('size')
        color = self.request.query_params.get('color')

        if subcategory_id:
            qs = qs.filter(subcategory_id=subcategory_id)
        if category_id:
            qs = qs.filter(subcategory__category_id=category_id)
        if gender:
            qs = qs.filter(subcategory__category__gender=gender)
        if visible and visible.lower() in ('1', 'true', 'yes'):
            qs = qs.filter(is_visible=True)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if size:
            qs = qs.filter(variants__size=size)
        if color:
            qs = qs.filter(variants__color_name=color)

        return qs.distinct()


class ProductDetailView(generics.RetrieveAPIView):
    """Детальная карточка товара + подборка похожих товаров"""
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.select_related(
        'subcategory', 'subcategory__category'
    ).prefetch_related('images', 'variants')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = self.get_object()
        related = Product.objects.filter(
            subcategory=obj.subcategory
        ).exclude(id=obj.id)[:4]
        context['related_products'] = related
        return context