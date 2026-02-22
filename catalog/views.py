from django.db.models import Prefetch, Count, Q
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from .models import Category, SubCategory, Product, ProductImage, ProductVariant
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)


class ProductPagination(PageNumberPagination):
    page_size = 16


class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Category.objects.all()

        params = self.request.query_params

        gender = params.get('gender')
        is_material = params.get('is_material')

        if gender in ('M', 'F'):
            qs = qs.filter(gender=gender)

        if is_material is not None:
            val = is_material.lower() in ('1', 'true', 'yes')
            qs = qs.filter(subcategories__is_material=val).distinct()

        return qs.order_by('order', 'name')


class SubCategoryListView(generics.ListAPIView):
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = SubCategory.objects.select_related(
            'category'
        ).prefetch_related(
            Prefetch(
                'products',
                queryset=Product.objects.filter(
                    is_visible=True
                ).prefetch_related(
                    Prefetch(
                        'images',
                        queryset=ProductImage.objects.order_by('order')
                    ),
                    Prefetch(
                        'variants',
                        queryset=ProductVariant.objects.only(
                            'id',
                            'product_id',
                            'color_name',
                            'color_hex',
                            'size',
                            'stock'
                        )
                    )
                )
            )
        )

        params = self.request.query_params

        category_id = params.get('category')
        show_on_main = params.get('show_on_main')
        gender = params.get('gender')

        if category_id:
            qs = qs.filter(category_id=category_id)

        if show_on_main and show_on_main.lower() in ('1', 'true', 'yes'):
            qs = qs.filter(show_on_main=True)

        if gender in ('M', 'F'):
            qs = qs.filter(category__gender=gender)

        if category_id:
            cat = Category.objects.filter(id=category_id).first()
            if cat and cat.name != 'Материалы':
                qs = qs.filter(is_material=False)

        return qs


class ProductListView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination

    SORT_MAP = {
        "default": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "newest": "-created_at",
    }

    def get_queryset(self):
        params = self.request.query_params

        qs = Product.objects.filter(
            is_visible=True
        ).select_related(
            "subcategory",
            "subcategory__category"
        ).prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("order")
            ),
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.only(
                    "id",
                    "product_id",
                    "color_name",
                    "color_hex",
                    "size",
                    "stock"
                )
            )
        )

        subcategory_id = params.get("subcategory")
        gender = params.get("gender")

        size_filters = params.getlist("size")
        color_filters = params.getlist("color")

        price_min = params.get("min_price")
        price_max = params.get("max_price")

        sort = params.get("sort", "default")

        if subcategory_id:
            qs = qs.filter(subcategory_id=subcategory_id)

        if gender in ("M", "F"):
            qs = qs.filter(subcategory__category__gender=gender)

        if size_filters:
            qs = qs.filter(variants__size__in=size_filters)

        if color_filters:
            qs = qs.filter(variants__color_hex__in=color_filters)

        if price_min:
            qs = qs.filter(price__gte=price_min)

        if price_max:
            qs = qs.filter(price__lte=price_max)

        order_field = self.SORT_MAP.get(sort, "-created_at")

        qs = qs.order_by(order_field).distinct()

        return qs


class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]

    queryset = Product.objects.select_related(
        'subcategory',
        'subcategory__category'
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.order_by('order')
        ),
        Prefetch(
            'variants',
            queryset=ProductVariant.objects.only(
                'id',
                'product_id',
                'color_name',
                'color_hex',
                'size',
                'stock'
            )
        )
    )

    def get_serializer_context(self):
        return {"request": self.request}


class SubCategoryDetailView(generics.RetrieveAPIView):
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.AllowAny]

    queryset = SubCategory.objects.select_related(
        'category'
    ).prefetch_related(
        Prefetch(
            'products',
            queryset=Product.objects.filter(
                is_visible=True
            ).prefetch_related(
                'images',
                'variants'
            )
        )
    )
