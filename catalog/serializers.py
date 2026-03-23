from rest_framework import serializers
from django.conf import settings
from .models import (
    Category,
    SubCategory,
    Product,
    ProductImage,
    ProductVariant,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'gender', 'order')


class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    products = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = (
            'id', 'name', 'size_model', 'cover_image', 'show_on_main',
            'is_material', 'description', 'order', 'category',
            'products', 'products_count'
        )

    def get_products(self, obj):
        request = self.context.get("request")

        if obj.is_material:
            products = obj.material_products.all()
        else:
            products = obj.products.filter(is_visible=True)

        return ProductListSerializer(products, many=True, context=self.context).data

    def get_products_count(self, obj):
        if obj.is_material:
            return obj.material_products.count()
        return obj.products.filter(is_visible=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'order')


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ('id', 'color_name', 'color_hex', 'size', 'stock')


class ProductListSerializer(serializers.ModelSerializer):
    main_image = serializers.ImageField()
    subcategory = serializers.PrimaryKeyRelatedField(read_only=True)
    gallery = serializers.SerializerMethodField()
    colors = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'price_rub',
            'price_kzt',
            'price_byn',
            'is_visible',
            'main_image',
            'gallery',
            'colors',
            'subcategory',
            'material',
        )

    # ---- Галерея (2-3 изображения) ----
    def get_gallery(self, obj):
        if not hasattr(obj, 'images'):
            return []

        request = self.context.get("request")
        base_url = request.build_absolute_uri("/") if request else settings.MEDIA_URL

        images = obj.images.all().order_by('order')[:3]

        return [
            {
                "id": img.id,
                "image": request.build_absolute_uri(img.image.url)
                if request
                else base_url.rstrip("/") + img.image.url
            }
            for img in images
            if img.image
        ]

    # ---- Уникальные цвета ----
    def get_colors(self, obj):
        if not hasattr(obj, 'variants'):
            return []

        unique = {}
        for v in obj.variants.all():
            if v.color_hex not in unique:
                unique[v.color_hex] = v.color_name

        return [
            {"name": name, "hex": hex_code}
            for hex_code, name in unique.items()
        ]


class SubCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = (
            'id',
            'name',
            'size_model',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    colors = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    similar_products = serializers.SerializerMethodField()

    subcategory = SubCategorySimpleSerializer(read_only=True)

    gender = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'description',
            'price_rub',
            'price_kzt',
            'price_byn',
            'is_visible',
            'main_image',
            'created_at',
            'material',
            'subcategory',
            'gender',
            'images',
            'variants',
            'colors',
            'sizes',
            'similar_products',
        )

    # ---------- Gender ----------
    def get_gender(self, obj):
        if obj.subcategory and obj.subcategory.category:
            return obj.subcategory.category.gender
        return None

    # ---------- Images ----------
    def get_images(self, obj):
        request = self.context.get("request")

        images = obj.images.all().order_by("order")

        result = []
        for img in images:
            if not img.image:
                continue

            if request:
                url = request.build_absolute_uri(img.image.url)
            else:
                url = settings.MEDIA_URL.rstrip("/") + img.image.url

            result.append({
                "id": img.id,
                "image": url
            })

        return result

    # ---------- Variants ----------
    def get_variants(self, obj):
        return [
            {
                "id": v.id,
                "color_name": v.color_name,
                "color_hex": v.color_hex,
                "size": v.size,
                "stock": v.stock,
            }
            for v in obj.variants.all()
        ]

    # ---------- Colors ----------
    def get_colors(self, obj):
        unique = {}

        for v in obj.variants.all():
            if v.color_hex not in unique:
                unique[v.color_hex] = v.color_name

        return [
            {"name": name, "hex": hex_code}
            for hex_code, name in unique.items()
        ]

    # ---------- Sizes ----------
    def get_sizes(self, obj):
        SIZE_ORDER = {
            ProductVariant.Sizes.XXS: 0, ProductVariant.Sizes.XS: 1,
            ProductVariant.Sizes.S: 2, ProductVariant.Sizes.M: 3,
            ProductVariant.Sizes.L: 4, ProductVariant.Sizes.XL: 5,
            ProductVariant.Sizes.XXL: 6, ProductVariant.Sizes.UNI: 7,
        }

        size_map = {}
        for v in obj.variants.all():
            size_map.setdefault(v.size, 0)
            size_map[v.size] += v.stock

        sorted_sizes = sorted(size_map.items(), key=lambda x: SIZE_ORDER.get(x[0], 99))

        return [{"size": size, "stock": stock} for size, stock in sorted_sizes]

    # ---------- Similar Products ----------
    def get_similar_products(self, obj):
        qs = (
            Product.objects
            .filter(
                subcategory=obj.subcategory,
                is_visible=True
            )
            .exclude(id=obj.id)
            .select_related('subcategory')
            .prefetch_related('images', 'variants')
            .order_by('-created_at')[:4]
        )

        return ProductListSerializer(
            qs,
            many=True,
            context=self.context
        ).data