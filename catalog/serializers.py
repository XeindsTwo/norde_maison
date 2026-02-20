from rest_framework import serializers
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

    class Meta:
        model = SubCategory
        fields = (
            'id',
            'name',
            'size_model',
            'cover_image',
            'show_on_main',
            'is_material',
            'description',
            'order',
            'category',
        )


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

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'price',
            'is_visible',
            'main_image',
            'subcategory',
            'material',
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    similar_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'description',
            'price',
            'is_visible',
            'main_image',
            'created_at',
            'subcategory',
            'material',
            'images',
            'variants',
            'similar_products',
        )

    def get_similar_products(self, obj):
        qs = Product.objects.filter(
            subcategory=obj.subcategory
        ).exclude(id=obj.id)[:4]
        return ProductListSerializer(qs, many=True, context=self.context).data